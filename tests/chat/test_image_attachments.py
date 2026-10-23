import asyncio
from io import BytesIO
import json
import pytest
from PIL import Image, ImageDraw, ImageFont
from packages.chat.attachments import extract_document, read_document, model_attachment_text, MARKER


def image_bytes():
    image = Image.new('RGB', (1000, 180), 'white')
    ImageDraw.Draw(image).text((25, 35), 'Dividend CNY 2000000', fill='black', font=ImageFont.load_default(size=42))
    out = BytesIO(); image.save(out, format='PNG')
    return out.getvalue()


def test_real_image_ocr_worker():
    payload = asyncio.run(read_document(image_bytes(), '.png'))
    assert payload['kind'] == 'image'
    assert '2000000' in payload['pages'][0]['text']
    assert payload['thumbnail'].startswith('data:image/jpeg;base64,')
    assert len(payload['thumbnail']) < 13000


def test_invalid_image_is_rejected():
    with pytest.raises(ValueError, match='attachment_invalid'):
        extract_document(b'not an image', '.png')


def test_oversized_image_is_rejected_before_ocr():
    out = BytesIO(); Image.new('L', (5000, 4100), 'white').save(out, format='PNG')
    with pytest.raises(ValueError, match='attachment_image_dimensions'):
        extract_document(out.getvalue(), '.png')


def test_display_thumbnail_is_excluded_from_model_context():
    text = 'Read this' + MARKER + json.dumps({'name': 'image.png', 'thumbnail':'data:image/jpeg;base64,AAAA',
                                            'pages': [{'page':1, 'text':'Dividend 2000000'}]})
    output = model_attachment_text(text)
    assert 'base64' not in output
    assert '2000000' in output
