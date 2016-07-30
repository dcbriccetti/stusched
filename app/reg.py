from datetime import datetime
import logging
from django.contrib import messages
from app.students import students_of_parent
from .models import Section, StudentSectionAssignment

log = logging.getLogger(__name__)


class RegistrationSetter:
    def __init__(self, request, section_id):
        self.request = request
        self.section = Section.objects.get(pk=section_id)
        self.pstudents = students_of_parent(request.user)
        self.pstudent_ids = set((s.id for s in self.pstudents))
        self.registered_children_ids = [ssa.student_id
            for ssa in StudentSectionAssignment.objects.filter(section_id=section_id) if ssa.student_id in self.pstudent_ids]

    def set(self, student, turn_on):
        current_assignment = StudentSectionAssignment.objects.filter(student=student, section=self.section)

        if turn_on and not current_assignment:
            new_ssa = StudentSectionAssignment(student=student, section=self.section, status=1, changed=datetime.now())
            new_ssa.save()
            msg = '%s enrolled in %s.' % (student.name, self.section)
            messages.add_message(self.request, messages.INFO, msg)
            log.info('%s: %s', self.request.user, msg)
        elif current_assignment and not turn_on:
            current_assignment.delete()
            msg = '%s unenrolled from %s.' % (student.name, self.section)
            messages.add_message(self.request, messages.INFO, msg)
            log.info('%s: %s', self.request.user, msg)


