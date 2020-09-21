from recipe.apps import RecipeConfig
from django.test import TestCase


class RecipeAppTest(TestCase):

    def test_app(self):
        test_recipe = RecipeConfig.name
        self.assertEqual(test_recipe, 'recipe')
