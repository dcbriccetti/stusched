from django.test import TestCase
from django.urls import reverse
from faker import Factory
from app.forms import NewUserForm, USER_EXISTS_ERROR_CODE

fake = Factory.create()


class LoginTest(TestCase):

    def test_cant_create_two_accounts_with_same_user(self):
        user_data = {
            'name':     fake.name(),
            'username': 'temp',
            'password': 'test',
            'email':    fake.safe_email()
        }
        response = self.client.post(reverse('log-in'), data=user_data)
        self.assertEqual(302, response.status_code)

        form = NewUserForm(data=user_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('username', USER_EXISTS_ERROR_CODE))
