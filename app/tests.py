from time import sleep
from django.test import TestCase, LiveServerTestCase
from django.contrib.auth.models import User
from app.models import Student, Parent, Course, Section, StudentSectionAssignment, SS_STATUS_APPLIED, SS_STATUS_ACCEPTED
from selenium import webdriver


class StudentTestCase(TestCase):
    def setUp(self):
        parent = Parent.objects.create(name='Dad')
        Student.objects.create(name='Dave', parent=parent)

    def test_is_a_student(self):
        self.assertEqual(Student.objects.count(), 1)


class BrowserTest(LiveServerTestCase):
    def test_login(self):
        username = "test-admin"
        password = "test-admin"
        superuser = User.objects.create_superuser(username=username, password=password, email="")
        browser = webdriver.Firefox()
        browser.get("%s/app/login" % self.live_server_url)
        browser.find_element_by_id("id_username").send_keys(username)
        browser.find_element_by_id("id_password").send_keys(password)
        browser.find_element_by_id('log-in').click()
        sleep(2)
        browser.quit()

    def test_accepted_student_sees_others(self):
        course = Course.objects.create(name='Python')
        section = Section.objects.create(course=course, start_time='2016-08-30T13:00:00', scheduled_status=1,
            hours_per_day=3, num_days=1)
        other_user = User.objects.create(username='mrsother', email='x@x.com')
        other_parent = Parent.objects.create(name='Mrs. Other', email='x@x.com')
        other_parent.users.add(other_user)
        other_stu = Student.objects.create(parent=other_parent, name='Student B', birthdate='2001-01-02', grade_from_age=5)
        other_ssa = StudentSectionAssignment.objects.create(student=other_stu, section=section, status=SS_STATUS_APPLIED)
        username = "mom"
        password = "mom"
        b = webdriver.Firefox()
        b.get("%s/app/login" % self.live_server_url)
        id  = b.find_element_by_id
        sel = b.find_element_by_css_selector
        sel('#create-form #id_name').send_keys('Mom')
        sel('#create-form #id_email').send_keys('daveb@davebsoft.com')
        sel('#create-form #id_username').send_keys(username)
        sel('#create-form #id_password').send_keys(password)
        sel('#create-form #create').click()
        b.get("%s/app/students" % self.live_server_url)
        id('add').click()
        id('id_name').send_keys('Student A')
        id('id_birthdate').send_keys('2001-05-06')
        id('id_grade_from_age').send_keys('5')
        sel('button').click()
        b.get("%s/app/sections" % self.live_server_url)
        sel('.chg-reg').click()
        sel('.apply').click()
        b.get("%s/app/sections" % self.live_server_url)
        self.assertEqual('Applied: Student A', sel('.student-names').text)
        sleep(.3)
        for ssa in StudentSectionAssignment.objects.all():
            ssa.status=SS_STATUS_ACCEPTED
            ssa.save()
        b.get("%s/app/sections" % self.live_server_url)
        self.assertEqual('Student A, Student B', sel('.student-names').text)
        sleep(2)
        b.quit()
