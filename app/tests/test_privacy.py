from time import sleep

from app.factories import StudentFactory, ParentFactory, SectionFactory, UserFactory
from django.test import LiveServerTestCase
from django.contrib.auth.models import User
from app.models import Course, StudentSectionAssignment, SS_STATUS_ACCEPTED
from selenium import webdriver


class Ups:
    'User, parent, student in a section'
    def __init__(self, section=None):
        self.user = UserFactory.create()
        self.parent = ParentFactory()
        self.parent.users.add(self.user)
        self.stu = StudentFactory.create(parent=self.parent)

        if section:
            StudentSectionAssignment.objects.create(student=self.stu, section=section, status=SS_STATUS_ACCEPTED)


class BrowserTest(LiveServerTestCase):

    def setUp(self):
        self.b = webdriver.Firefox()

    def tearDown(self):
        self.b.quit()

    def test_accepted_student_sees_others(self):
        'The parent of a student accepted into a section can see all accepted students in that section.'

        section = SectionFactory.create(course=Course.objects.create(name='Python'))
        u1 = Ups(section)
        u2 = Ups(section)

        self.log_in(u1.user.username)
        self.b.get("%s/app/sections" % self.live_server_url)
        expected_names = sorted([u1.stu.name, u2.stu.name])
        self.assertEqual(', '.join(expected_names), self.student_names())

    def test_staff_sees_all(self):
        'A staff user can see all students in a section.'

        section = SectionFactory.create(course=Course.objects.create(name='Python'))
        u1 = Ups(section)
        User.objects.create_superuser(username='admin', password='password', email='')

        self.log_in(u1.user.username)
        self.b.get("%s/app/sections" % self.live_server_url)
        expected_names = sorted([u1.stu.name])
        self.assertEqual(', '.join(expected_names), self.student_names())

    def test_student_not_in_section_sees_no_names(self):
        section = SectionFactory.create(course=Course.objects.create(name='Python'))
        u1 = Ups(section)
        u2 = Ups()

        self.log_in(u2.user.username)
        self.b.get("%s/app/sections" % self.live_server_url)
        self.assertEqual('', self.student_names())

    def student_names(self):
        return self.b.find_element_by_css_selector('.student-names').text

    def log_in(self, username):
        self.b.get("%s/app/login" % self.live_server_url)
        sel = self.b.find_element_by_css_selector
        sel('#log-in-form #id_username').send_keys(username)
        sel('#log-in-form #id_password').send_keys('password')
        sel('#log-in-form #log-in').click()
        return sel
