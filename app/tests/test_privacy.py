from os import environ
from time import sleep

from app.factories import StudentFactory, ParentFactory, SectionFactory, UserFactory
from django.test import LiveServerTestCase
from django.contrib.auth.models import User
from app.models import Course, StudentSectionAssignment, SS_STATUS_ACCEPTED, SS_STATUS_APPLIED
from selenium import webdriver


class Ups:
    'User, parent, student in a section'
    def __init__(self, section=None, status=SS_STATUS_ACCEPTED):
        self.user = UserFactory.create()
        self.parent = ParentFactory()
        self.parent.users.add(self.user)
        self.stu = StudentFactory.create(parent=self.parent)

        if section:
            StudentSectionAssignment.objects.create(student=self.stu, section=section, status=status)


class BrowserTest(LiveServerTestCase):

    def setUp(self):
        self.b = webdriver.Firefox()
        self.b.implicitly_wait(1)

    def tearDown(self):
        self.b.quit()

    def test_admin_only_for_admin(self):
        def texts(sel):
            return [el.text for el in self.b.find_elements_by_css_selector(sel)]
        def nav_texts():
            return texts('.nav li a')
        def admin_page_not_found():
            b.get("%s/admin" % self.app_url())
            self.assertIn('Not Found', texts('h1'))

        b = self.b
        admin_page_not_found()

        b.get(self.app_url())
        self.assertNotIn('Admin', nav_texts())

        User.objects.create_superuser(username='admin', password='password', email='')
        self.log_in('admin')
        b.get(self.app_url())
        self.assertIn('Admin', nav_texts())

        user = UserFactory.create()
        self.log_in(user.username)
        b.get(self.app_url())
        self.assertNotIn('Admin', nav_texts())

        admin_page_not_found()

    def app_url(self):
        return self.live_server_url + environ['APP_PATH']

    def test_accepted_student_sees_others(self):
        'The parent of a student accepted into a section can see all accepted students in that section.'

        section = SectionFactory.create(course=Course.objects.create(name='Python'))
        u1 = Ups(section)
        u2 = Ups(section)

        self.log_in(u1.user.username)
        self.b.get(self.sections_url())
        expected_names = sorted([u1.stu.name, u2.stu.name])
        self.assertEqual(', '.join(expected_names), self.student_names())

    def sections_url(self):
        return self.app_url() + "/sections"

    def test_staff_sees_all(self):
        'A staff user can see all students in a section.'

        su = User.objects.create_superuser(username='admin', password='password', email='')

        section = SectionFactory.create(course=Course.objects.create(name='Python'))
        names = self.names_of_many_upses(section)

        self.log_in(su.username)
        self.b.get(self.sections_url())
        self.assertEqual(', '.join(names), self.student_names())

    def test_student_not_in_section_sees_no_names(self):
        section = SectionFactory.create(course=Course.objects.create(name='Python'))
        names = self.names_of_many_upses(section)
        not_in_section_ups = Ups()

        self.log_in(not_in_section_ups.user.username)
        self.b.get(self.sections_url())
        self.assertEqual('', self.student_names())

    def test_applied_student_sees_no_names(self):
        section = SectionFactory.create(course=Course.objects.create(name='Python'))
        names = self.names_of_many_upses(section)
        applied_ups = Ups(section, status=SS_STATUS_APPLIED)

        self.log_in(applied_ups.user.username)
        self.b.get(self.sections_url())
        self.assertEqual('', self.student_names())

    def student_names(self):
        sleep(5)
        return self.b.find_element_by_css_selector('.student-names').text

    def names_of_many_upses(self, section):
        return sorted([Ups(section).stu.name for _ in range(6)])

    def log_in(self, username):
        self.b.get(self.app_url() + "/login")
        sel = self.b.find_element_by_css_selector
        sel('#log-in-form #id_username').send_keys(username)
        sel('#log-in-form #id_password').send_keys('password')
        sel('#log-in-form #log-in').click()
        return sel
