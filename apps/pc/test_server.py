"""Exercise pairing, API authentication, file access and origin protection."""
import unittest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from apps.pc.server import install_studio


class PairingTests(unittest.TestCase):
    def setUp(self):
        engine = FastAPI()
        @engine.get("/api/v1/tasks")
        def tasks(request: Request):
            return {"key": request.headers.get("x-api-key")}
        @engine.get("/tasks/result.mp4")
        def result(request: Request):
            return {"key": request.headers.get("x-api-key")}
        install_studio(engine, "engine-secret", "123456789012")
        self.client = TestClient(engine, base_url="http://192.168.1.10:8765")

    def pair(self):
        return self.client.post("/pair", json={"code": "1234 5678 9012"})

    def test_pairing_protects_api_and_generated_files(self):
        self.assertEqual(self.client.get("/api/v1/tasks").status_code, 401)
        self.assertEqual(self.client.get("/tasks/result.mp4").status_code, 401)
        response = self.pair()
        self.assertEqual(response.status_code, 200)
        self.assertIn("HttpOnly", response.headers["set-cookie"])
        self.assertEqual(self.client.get("/api/v1/tasks").json(), {"key": "engine-secret"})
        self.assertEqual(self.client.get("/tasks/result.mp4").status_code, 200)
        self.client.post("/unpair")
        self.assertEqual(self.client.get("/tasks/result.mp4").status_code, 401)

    def test_invalid_codes_are_rate_limited(self):
        for _ in range(5):
            self.assertEqual(self.client.post("/pair", json={"code": "wrong"}).status_code, 401)
        self.assertEqual(self.pair().status_code, 429)

    def test_cross_origin_and_rebinding_are_rejected(self):
        self.assertEqual(self.client.post("/pair", json={"code": "123456789012"}, headers={"origin": "https://evil.example"}).status_code, 403)
        self.assertEqual(self.client.get("/", headers={"host": "evil.example"}).status_code, 400)

    def test_unpaired_frontend_is_served(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/studio.js").status_code, 200)
        self.assertIn("frame-ancestors 'none'", self.client.get("/").headers["content-security-policy"])

    def test_pairing_session_does_not_survive_restart(self):
        self.pair()
        another = FastAPI()
        install_studio(another, "engine-secret", "123456789012")
        restarted = TestClient(another, base_url="http://192.168.1.10:8765")
        restarted.cookies.update(self.client.cookies)
        self.assertEqual(restarted.get("/studio-status").status_code, 401)

    def test_invalid_pairing_payload_is_handled(self):
        self.assertEqual(self.client.post("/pair", content="not JSON").status_code, 400)
        self.assertEqual(self.client.post("/pair", content="{}", headers={"content-length": "bad"}).status_code, 400)
        self.assertEqual(self.client.post("/pair", content="x" * 2048).status_code, 413)


if __name__ == "__main__":
    unittest.main()
