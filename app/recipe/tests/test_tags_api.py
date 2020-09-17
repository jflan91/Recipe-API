from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    """Test public api tags"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login required to retrieve tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test user tags"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@email.com',
            'testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test tag retrieval"""
        Tag.objects.create(user=self.user, name='Italian')
        Tag.objects.create(user=self.user, name='German')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_user_limited_tags(self):
        """Test only retrieve authenticated enduser tags"""
        user2 = get_user_model().objects.create_user(
            'test2',
            'testpass123'
        )
        Tag.objects.create(user=user2, name='Seafood')
        tag = Tag.objects.create(user=self.user, name='Quick Meals')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag(self):
        """Test creating new tag"""
        payload = {'name': 'Test'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_tag_creation_invalid(self):
        """Test tag creation with invalid input"""

        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_by_recipe(self):
        """Test recipe tag retrieval by recipe"""
        tag1 = Tag.objects.create(user=self.user, name='Entree')
        tag2 = Tag.objects.create(user=self.user, name='Dessert')
        recipe = Recipe.objects.create(
            title='Italian Chicken',
            time_minutes=30,
            price=10.00,
            user=self.user
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_unique(self):
        """Test filtering tags returns unique items"""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        Tag.objects.create(user=self.user, name='Dinner')
        recipe1 = Recipe.objects.create(
            title='Bacon Omelette',
            time_minutes=8,
            price=5.00,
            user=self.user
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title='Biscuits and Sausage Gravy',
            time_minutes=20,
            price=8.00,
            user=self.user
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
