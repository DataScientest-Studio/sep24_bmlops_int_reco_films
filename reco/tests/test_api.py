import unittest
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_token_endpoint(self):
        response = self.client.post("/token", data={"username": "johndoe", "password": "fakehashedpassword"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())

    def test_recommendation_endpoint(self):
        token_response = self.client.post("/token", data={"username": "johndoe", "password": "fakehashedpassword"})
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.post("/recommend", headers=headers, json={"candidate_movie_ids": [1,2,3], "top_n": 2})
        self.assertEqual(response.status_code, 200)
        self.assertIn("recommended_movie_ids", response.json())

client = TestClient(app)

def test_register_user():
    response = client.post("/register", json={"username": "testuser", "email": "test@example.com", "password": "testpassword"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login():
    response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_get_recommendations():
    login_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/recommendations", headers=headers)
    assert response.status_code == 200
    assert "recommendations" in response.json()

def test_submit_feedback():
    login_response = client.post("/token", data={"username": "testuser", "password": "testpassword"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/feedback", json={"movie_id": 1, "rating": 4.5}, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Feedback submitted successfully"

if __name__ == '__main__':
    unittest.main()
