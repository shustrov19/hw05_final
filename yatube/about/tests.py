from http import HTTPStatus

from django.test import Client, TestCase
from django.views.generic.base import TemplateView

AUTHOR_PAGE = '/about/author/'
TECH_PAGE = '/about/tech/'
TEMPLATE_URL_NAMES = {
    AUTHOR_PAGE: 'about/author.html',
    TECH_PAGE: 'about/tech.html'
}


class StaticPagesURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов"""
        for url in TEMPLATE_URL_NAMES:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблонов для urls."""
        for url, template in TEMPLATE_URL_NAMES.items():
            with self.subTest(address=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)


class AboutAuthor(TemplateView):
    template_name = AUTHOR_PAGE


class AboutTech(TemplateView):
    template_name = TECH_PAGE
