from app.adminviews import email_parents
from app.models import Course, StudentSectionAssignment, SS_STATUS_APPLIED
from django.test import TestCase
from app.factories import StudentFactory, ParentFactory, UserFactory, SectionFactory


class EmailTest(TestCase):
    def test_email_goes_to_right_parents(self):
        user1 = UserFactory.create()
        self.client.login(username=user1.username, password='password')
        parent1 = ParentFactory()
        parent1.users.add(user1)
        stu1a = StudentFactory.create(parent=parent1)
        stu1b = StudentFactory.create(parent=parent1)

        user2 = UserFactory.create()
        self.client.login(username=user2.username, password='password')
        parent2 = ParentFactory()
        parent2.users.add(user2)
        stu2a = StudentFactory.create(parent=parent2)
        stu2b = StudentFactory.create(parent=parent2)

        course1 = Course(name='Python')
        course1.save()
        stu1a.wants_courses.add(course1)
        py_sec = SectionFactory(course=course1)
        
        parents = email_parents(())  # No filters, so all parents should be included
        self.assertIn(parent1, parents)
        self.assertIn(parent2, parents)

        parents = email_parents((), send_only_upcoming=True)  # No parents have students in upcoming sections
        self.assertNotIn(parent1, parents)
        self.assertNotIn(parent2, parents)

        StudentSectionAssignment(student=stu1a, section=py_sec, status=SS_STATUS_APPLIED).save()

        parents = email_parents((), send_only_upcoming=True)  # parent1 now has a student in an upcoming section
        self.assertIn(parent1, parents)
        self.assertNotIn(parent2, parents)

        parents = email_parents((), send_only_wanted_upcoming=True)
        self.assertNotIn(parent1, parents)
        self.assertNotIn(parent2, parents)

        parents = email_parents((course1.id,), send_only_wanted_upcoming=True)
        self.assertIn(parent1, parents)
        self.assertNotIn(parent2, parents)
