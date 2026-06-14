from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_format_endpoint_formats_python_code():
    response = client.post("/format", json={"code": "x=1\n", "language": "python"})
    assert response.status_code == 200
    assert response.json() == {"code": "x = 1\n"}


def test_format_endpoint_returns_400_on_syntax_error():
    response = client.post(
        "/format", json={"code": "def foo(:\n", "language": "python"}
    )
    assert response.status_code == 400
