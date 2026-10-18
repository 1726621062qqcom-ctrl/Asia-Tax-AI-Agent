import pytest
from fastapi.testclient import TestClient
from apps.api.main import create_app
from packages.consultation.service import ConsultationService

HEADERS={'X-FSIE-Demo':'1'}

@pytest.fixture
def client():
    with TestClient(create_app(ConsultationService())) as c:
        yield c


def begin(client):
    return client.post('/api/session',headers=HEADERS,json={'synthetic_acknowledged':True})


def send(client,message='香港 FSIE 对境外股息有哪些规定？',id='request_001'):
    return client.post('/api/chat',headers=HEADERS,json={'message':message,'request_id':id})


def test_health_does_not_leak_database_or_keys(client):
    assert client.get('/health').json()=={'status':'ok','release_level':'L0'}
    config=client.get('/api/config').json()
    assert config['mode']=='local_research'
    assert 'database' not in str(config) and 'api_key' not in str(config)


def test_serves_ui_and_static_assets(client):
    r=client.get('/')
    assert r.status_code==200 and '从公司情况' in r.text
    assert 'frame-ancestors' in r.headers['content-security-policy']
    for path in ['/static/app.js','/static/app.css']:
        assert client.get(path).status_code==200


def test_session_ack_and_origin_guards(client):
    assert client.post('/api/session',json={'synthetic_acknowledged':True}).status_code==403
    assert client.post('/api/session',headers=HEADERS,json={'synthetic_acknowledged':False}).status_code==422
    assert client.post('/api/session',headers={**HEADERS,'Origin':'https://evil.example'},json={'synthetic_acknowledged':True}).status_code==403
    assert client.get('/health',headers={'Host':'evil.example'}).status_code==400
    assert send(client).status_code==401


def test_chat_idempotency_and_clear(client):
    created=begin(client)
    assert 'HttpOnly' in created.headers['set-cookie']
    first=send(client)
    assert first.status_code==200 and first.json()['citations']
    repeated=send(client)
    assert repeated.json()==first.json()
    assert send(client,'不同内容').status_code==409
    client.delete('/api/session',headers=HEADERS)
    assert send(client,id='request_002').status_code==401


def test_empty_and_oversized_inputs(client):
    begin(client)
    assert send(client,'   ').status_code==422
    assert send(client,'字'*4001).status_code==422


def test_twenty_turn_limit(client):
    begin(client)
    for i in range(20):
        assert send(client,id=f'request_{i:03}').status_code==200
    assert send(client,id='request_021').status_code==409


def test_second_browser_does_not_read_first_session(client):
    begin(client)
    send(client,'假设我们持有境外子公司60%股份。')
    with TestClient(client.app) as second:
        assert send(second).status_code==401
        begin(second)
        result=send(second)
        assert result.status_code==200 and result.json()['facts']==[]


def test_request_in_flight_is_not_duplicated(client):
    begin(client)
    session=client.app.state.sessions.get(client.cookies.get('fsie_demo_session'))
    session.lock.acquire()
    try:
        assert send(client).status_code==409
        assert session.messages==[]
    finally:
        session.lock.release()


def test_model_not_enabled_by_credentials_alone(monkeypatch):
    from packages.persistence.config import get_settings
    from packages.model_adapter.client import get_model_config
    monkeypatch.setenv('FSIE_MODEL_BASE_URL','https://example.invalid/v1')
    monkeypatch.setenv('FSIE_MODEL_API_KEY','test-secret')
    monkeypatch.setenv('FSIE_MODEL_NAME','test-model')
    monkeypatch.setenv('FSIE_CHAT_ENABLE_MODEL','false')
    get_settings.cache_clear();get_model_config.cache_clear()
    try:
        with TestClient(create_app()) as c:
            assert c.get('/api/config').json()['mode']=='local_research'
    finally:
        get_settings.cache_clear();get_model_config.cache_clear()


def test_deployed_hostname_and_https_session(monkeypatch):
    from packages.persistence.config import get_settings
    monkeypatch.setenv('FSIE_ALLOWED_HOSTS', '["127.0.0.1","taxrora.onrender.com"]')
    get_settings.cache_clear()
    try:
        with TestClient(create_app(ConsultationService()), base_url='https://taxrora.onrender.com') as c:
            assert c.get('/').status_code == 200
            assert c.get('/health', headers={'Host': 'untrusted.example'}).status_code == 400
            response = c.post('/api/session', headers={**HEADERS, 'Origin': 'https://taxrora.onrender.com'},
                              json={'synthetic_acknowledged': True})
            assert response.status_code == 200
            assert 'Secure' in response.headers['set-cookie']
            assert send(c).status_code == 200
    finally:
        get_settings.cache_clear()


def test_render_hostname_and_tls_termination(monkeypatch):
    from packages.persistence.config import get_settings
    monkeypatch.setenv('RENDER_EXTERNAL_HOSTNAME', 'taxrora-app.onrender.com')
    monkeypatch.setenv('FSIE_SECURE_COOKIES', 'true')
    get_settings.cache_clear()
    try:
        with TestClient(create_app(ConsultationService()), base_url='http://taxrora-app.onrender.com') as c:
            assert c.get('/').status_code == 200
            assert c.get('/health', headers={'Host': 'another-app.onrender.com'}).status_code == 400
            response = c.post('/api/session', headers={**HEADERS, 'Origin': 'https://taxrora-app.onrender.com'},
                              json={'synthetic_acknowledged': True})
            assert response.status_code == 200
            assert 'Secure' in response.headers['set-cookie']
    finally:
        get_settings.cache_clear()
