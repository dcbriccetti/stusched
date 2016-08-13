from django.test import TestCase
from app.models import NewsItem


class NewsTest(TestCase):
    def setUp(self):
        self.item = NewsItem.objects.create(text='*Here* is an item.')

    def tearDown(self):
        self.item.delete()

    def test_can_fetch_item(self):
        item = NewsItem.objects.first()
        self.assertEqual('<p><em>Here</em> is an item.</p>', item.as_html())
