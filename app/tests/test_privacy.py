from time import sleep
from app.factories import StudentFactory, ParentFactory
from django.test import TestCase, LiveServerTestCase
from django.contrib.auth.models import User
from app.models import Student, Parent, Course, Section, StudentSectionAssignment, SS_STATUS_APPLIED, SS_STATUS_ACCEPTED
from selenium import webdriver


class BrowserTest(LiveServerTestCase):
    def test_accepted_student_sees_others(self):
        course = Course.objects.create(name='Python')
        section = Section.objects.create(course=course, start_time='2016-08-30T13:00:00', scheduled_status=1,
            hours_per_day=3, num_days=1)
        other_user = User.objects.create(username='mrsother', email='x@x.com')
        other_parent = ParentFactory()
        other_parent.users.add(other_user)
        other_stu = StudentFactory.create(parent=other_parent)
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
        for ssa in StudentSectionAssignment.objects.all():
            ssa.status=SS_STATUS_ACCEPTED
            ssa.save()
        b.get("%s/app/sections" % self.live_server_url)
        student_names = sel('.student-names').text
        b.quit()
        self.assertEqual('Student A, ' + other_stu.name, student_names)
