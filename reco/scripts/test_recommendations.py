import os
import sys
import requests
import subprocess
import time
import signal
import socket

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

API_URL = "http://localhost:8000"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_api_server():
    if is_port_in_use(8000):
        print("API server is already running.")
        return None
    process = subprocess.Popen(["python", "-m", "src.api.main"])
    time.sleep(5)  # Give the server some time to start
    return process

def stop_api_server(process):
    if process:
        os.kill(process.pid, signal.SIGTERM)

def test_recommendation_system():
    print("Testing the Movie Recommendation System")
    print("---------------------------------------")

    api_process = start_api_server()

    try:
        # 1. Register a new user
        print("\n1. Registering a new user...")
        register_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword"
        }
        try:
            response = requests.post(f"{API_URL}/register", json=register_data)
            response.raise_for_status()
            print(f"Registration response: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Error during registration: {e}")
            return

        # 2. Login
        print("\n2. Logging in...")
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }
        try:
            response = requests.post(f"{API_URL}/token", data=login_data)
            response.raise_for_status()
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("Login successful")
        except requests.exceptions.RequestException as e:
            print(f"Error during login: {e}")
            return

        # 3. Get recommendations
        print("\n3. Getting recommendations...")
        try:
            response = requests.get(f"{API_URL}/recommendations", headers=headers)
            response.raise_for_status()
            recommendations = response.json()["recommendations"]
            print(f"Received {len(recommendations)} recommendations")
        except requests.exceptions.RequestException as e:
            print(f"Error getting recommendations: {e}")
            return

        # 4. Submit feedback
        print("\n4. Submitting feedback...")
        if recommendations:
            feedback_data = {
                "movie_id": recommendations[0]["movieId"],
                "rating": 4.5
            }
            try:
                response = requests.post(f"{API_URL}/feedback", json=feedback_data, headers=headers)
                response.raise_for_status()
                print(f"Feedback submission response: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"Error submitting feedback: {e}")

        # 5. Get user feedback
        print("\n5. Getting user feedback...")
        try:
            response = requests.get(f"{API_URL}/feedback", headers=headers)
            response.raise_for_status()
            feedback = response.json()["feedback"]
            print(f"User feedback: {feedback}")
        except requests.exceptions.RequestException as e:
            print(f"Error getting user feedback: {e}")

        print("\nTest completed successfully")
    finally:
        stop_api_server(api_process)

if __name__ == "__main__":
    test_recommendation_system()
