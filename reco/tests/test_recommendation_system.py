import unittest
from src.models.collaborative_filtering import recommend_movies, find_similar_movies
from src.models.user_feedback import collect_user_feedback, get_user_feedback
from src.data.database import get_session, User, Movie, Rating

class TestRecommendationSystem(unittest.TestCase):
    def setUp(self):
        self.model_path = 'models/collaborative_filtering_model.pkl'
        self.session = get_session()

    def tearDown(self):
        self.session.close()

    def test_recommend_movies(self):
        user_id = 1
        recommendations = recommend_movies(user_id, self.model_path)
        self.assertIsInstance(recommendations, list)
        self.assertTrue(len(recommendations) > 0)

    def test_find_similar_movies(self):
        movie_id = 1
        similar_movies = find_similar_movies(movie_id, self.model_path)
        self.assertIsInstance(similar_movies, list)
        self.assertTrue(len(similar_movies) > 0)

    def test_user_feedback(self):
        user_id = 1
        movie_id = 1
        rating = 4.5
        success = collect_user_feedback(user_id, movie_id, rating)
        self.assertTrue(success)

        feedback = get_user_feedback(user_id)
        self.assertIsInstance(feedback, list)
        self.assertTrue(len(feedback) > 0)

if __name__ == '__main__':
    unittest.main()
