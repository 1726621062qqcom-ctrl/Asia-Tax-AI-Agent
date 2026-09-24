"""Local Hong Kong FSIE consultation demo and research API."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from packages.consultation.knowledge import KnowledgeBase
from packages.consultation.schemas import ChatRequest, SessionCreate
from packages.consultation.service import ConsultationService
from packages.consultation.sessions import SessionStore
from packages.model_adapter.client import ModelConfig, OpenAICompatibleClient, get_model_config
from packages.persistence.config import get_settings

STATIC = Path(__file__).parent/'static'
COOKIE = 'fsie_demo_session'


def create_app(service: ConsultationService | None = None, store: SessionStore | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        if app.state.service is None:
            settings = get_settings()
            client = None
            config = get_model_config()
            if settings.chat_enable_model and config.is_configured:
                # Two bounded calls per turn; no automatic retry storm in interactive demo.
                client = OpenAICompatibleClient(ModelConfig(config.base_url,config.api_key,config.model_name,
                    timeout_seconds=min(config.timeout_seconds,30),max_retries=0))
            app.state.service = ConsultationService(client=client)
        yield

    app = FastAPI(title='Asia Tax AI — 香港 FSIE 研究对话',version='0.2.0',lifespan=lifespan)
    app.state.service = service
    app.state.sessions = store or SessionStore()
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','[::1]','testserver'])

    @app.middleware('http')
    async def local_boundary(request: Request, call_next):
        if request.method in ('POST','DELETE','PUT','PATCH'):
            origin = request.headers.get('origin')
            if request.headers.get('x-fsie-demo') != '1' or (origin and (
                urlparse(origin).netloc != request.headers.get('host') or urlparse(origin).scheme not in ('http','https'))):
                from fastapi.responses import JSONResponse
                return JSONResponse({'detail':'请求来源不受支持，请从本地 Demo 页面操作。'},status_code=403)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response

    def session_for(request):
        try:
            return app.state.sessions.get(request.cookies.get(COOKIE))
        except KeyError:
            raise HTTPException(401,'对话已过期或尚未开始，请新建对话。')

    @app.get('/health')
    def health():
        return {'status':'ok','release_level':'L0'}

    @app.get('/api/config')
    def config():
        service = app.state.service
        return dict(mode='model_research' if service.client else 'local_research',
            model=service.client.config.model_name if service.client else None,
            corpus_version=service.knowledge.data['version'],
            legal_coverage_cutoff=service.knowledge.data['legal_coverage_cutoff'],
            retrieved_at=service.knowledge.data['retrieved_at'],
            drift=service.knowledge.data['drift_from_manifest'],
            scope='香港 FSIE · 境外股息',max_turns=20)

    @app.post('/api/session')
    def create_session(body: SessionCreate, request: Request, response: Response):
        try:
            new = app.state.sessions.create(body.synthetic_acknowledged)
        except OverflowError:
            raise HTTPException(429,'当前对话数量已达上限，请稍后再试。')
        app.state.sessions.delete(request.cookies.get(COOKIE))
        response.set_cookie(COOKIE,new.token,httponly=True,samesite='strict',max_age=3600,
                            secure=request.url.scheme=='https',path='/api')
        return {'created':True}

    @app.delete('/api/session')
    def clear_session(request: Request, response: Response):
        app.state.sessions.delete(request.cookies.get(COOKIE))
        response.delete_cookie(COOKIE,path='/api')
        return {'cleared':True}

    @app.post('/api/chat')
    def chat(body: ChatRequest, request: Request):
        message = body.message.strip()
        if not message:
            raise HTTPException(422,'请输入问题。')
        session = session_for(request)
        if not session.lock.acquire(blocking=False):
            raise HTTPException(409,'上一条消息仍在处理，请稍候。')
        try:
            if body.request_id in session.responses:
                previous_message,answer = session.responses[body.request_id]
                if previous_message != message:
                    raise HTTPException(409,'重复请求编号对应不同内容，请重新发送。')
                return answer
            if len(session.messages) >= 20:
                raise HTTPException(409,'本轮已达到 20 条消息，请新建对话后继续。')
            answer = app.state.service.reply(message,session.facts,session.messages,len(session.messages)+1,
                                             synthetic_acknowledged=session.synthetic_acknowledged)
            if not session.active:
                raise HTTPException(409,'此对话已被清空。')
            session.messages.append(message)
            session.facts = answer.facts
            session.responses[body.request_id] = (message,answer)
            return answer
        finally:
            session.lock.release()

    @app.get('/')
    def index():
        return FileResponse(STATIC/'index.html')

    app.mount('/static',StaticFiles(directory=STATIC),name='static')
    return app


app = create_app()
