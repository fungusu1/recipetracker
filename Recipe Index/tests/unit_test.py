import unittest
import os
import sys

# Ensure project root is on PYTHONPATH so we can import models and app
# tests/unit_test.py lives in <project_root>/tests/, so parent dir is project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from models import Recipe, Rating, User
from app import allowed_file


class TestRecipeMethods(unittest.TestCase):
    def test_recipe_average_rating_no_ratings(self):
        # When there are no ratings, average should be 0.0 and of float type
        recipe = Recipe()
        recipe.ratings = []
        avg = recipe.average_rating
        self.assertEqual(avg, 0.0)
        self.assertIsInstance(avg, float)

    def test_recipe_average_rating_multiple_ratings(self):
        # Multiple ratings yield correct average
        r1 = Rating(rating=2)
        r2 = Rating(rating=5)
        r3 = Rating(rating=3)
        recipe = Recipe()
        recipe.ratings = [r1, r2, r3]
        expected = (2 + 5 + 3) / 3
        self.assertAlmostEqual(recipe.average_rating, expected, places=3)


class TestUserMethods(unittest.TestCase):
    def test_user_total_recipes_zero_and_nonzero(self):
        user = User()
        # No recipes
        user.recipes = []
        self.assertEqual(user.total_recipes, 0)
        # Some recipes
        user.recipes = [Recipe(), Recipe(), Recipe()]
        self.assertEqual(user.total_recipes, 3)

    def test_user_average_recipe_rating_various(self):
        user = User()
        # No recipes => zero
        user.recipes = []
        self.assertEqual(user.average_recipe_rating, 0.0)

        # Recipes present but none have ratings => zero
        empty_recipe = Recipe()
        empty_recipe.ratings = []
        user.recipes = [empty_recipe, empty_recipe]
        self.assertEqual(user.average_recipe_rating, 0.0)

        # Mixed: ignore recipes without ratings
        r1 = Recipe(); r1.ratings = [Rating(rating=4), Rating(rating=2)]  # avg = 3
        r2 = Recipe(); r2.ratings = [Rating(rating=5)]                   # avg = 5
        r3 = Recipe(); r3.ratings = []                                   # ignored
        user.recipes = [r1, r2, r3]
        expected = (3 + 5) / 2
        self.assertAlmostEqual(user.average_recipe_rating, expected, places=3)


class TestAllowedFile(unittest.TestCase):
    def test_allowed_file_various_extensions(self):
        cases = [
            ("photo.png", True),
            ("photo.PNG", True),
            ("image.jpeg", True),
            ("document.pdf", False),
            (".env", False),
            ("archive.tar.gz", False),
            ("noextension", False),
            ("image.", False),
            ("image.jpG  ", False),
        ]
        for filename, expected in cases:
            with self.subTest(filename=filename):
                self.assertEqual(allowed_file(filename), expected)


if __name__ == '__main__':
    unittest.main()
