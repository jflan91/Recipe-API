from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """Create and return sample recipe"""
    defaults = {
        'title': 'test recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test public recipe api"""

    def setUp(self):
        self.client_class = APIClient()

    def test_login_required(self):
        """Test that login is required"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test recipe api for authorized user"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@email.com',
            'testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_get_recipe(self):
        """Test recipe retrieval for authorized user"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_user_limited_recipes(self):
        user2 = get_user_model().objects.create_user(
            'test2',
            'testpass123'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
