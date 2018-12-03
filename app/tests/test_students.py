from app.models import Course
from django.test import TestCase
from django.urls import reverse
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
        course1 = Course(name='Python')
        course1.save()
        stu1.wants_courses.add(course1)

        response = self.client.get(reverse('students') + '?wants=%i' % course1.id)
        self.assertEqual(200, response.status_code)

        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        self.assertIn(stu1.name, text)
        self.assertNotIn(stu2.name, text)
