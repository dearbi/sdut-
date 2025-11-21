import io
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_recognize_endpoint():
    buf = io.BytesIO()
    Image.new('RGB', (256, 256), color=(120, 80, 60)).save(buf, format='PNG')
    buf.seek(0)
    files = { 'image': ('test.png', buf, 'image/png') }
    resp = client.post('/api/v1/image/recognize', files=files)
    assert resp.status_code == 200
    j = resp.json()
    assert 'tumor_type' in j
    assert 'abcde' in j