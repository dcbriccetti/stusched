from django.core.urlresolvers import reverse
from django.test import TestCase
from bs4 import BeautifulSoup
from app.factories import StudentFactory, ParentFactory, UserFactory


class StudentsTest(TestCase):
    def test_can_view_students(self):
        user = UserFactory.create()
        self.client.login(username=user.username, password='password')
        parent = ParentFactory()
        parent.users.add(user)
        stu1 = StudentFactory.create(parent=parent)
        stu2 = StudentFactory.create(parent=parent)

        response = self.client.get(reverse('students'))
        self.assertEqual(200, response.status_code)

        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        for stu in stu1, stu2:
            self.assertIn(stu.name, text)
