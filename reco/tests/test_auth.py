# tests/test_auth.py

import unittest
from src.api.auth import get_password_hash, verify_password

class TestAuth(unittest.TestCase):
    def test_password_hashing(self):
        password = 'testpassword'
        hashed = get_password_hash(password)
        self.assertTrue(verify_password(password, hashed))

if __name__ == '__main__':
    unittest.main()
