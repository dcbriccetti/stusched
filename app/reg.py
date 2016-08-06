from datetime import datetime
import logging
from django.contrib import messages
from app.students import students_of_parent
from .models import Section, StudentSectionAssignment, augmented_student_section_assignments

log = logging.getLogger(__name__)


class StudentWithAssignment:
    def __init__(self, student, augmented_student_section_assignment):
        self.student = student
        self.assa = augmented_student_section_assignment  # May be None


class RegistrationSetter:
    def __init__(self, request, section_id):
        self.request = request
        self.section = Section.objects.get(pk=section_id)
        self.children = students_of_parent(request.user)
        children_ids = set((s.id for s in self.children))
        child_aug_ssas = [assa for assa in augmented_student_section_assignments(section_id)
                          if assa.ssa.student_id in children_ids]
        assas_by_student = {assa.ssa.student: assa for assa in child_aug_ssas}
        self.swas = [StudentWithAssignment(student, assas_by_student.get(student)) for student in self.children]

    def set(self, student, turn_on):
        current_assignment = StudentSectionAssignment.objects.filter(student=student, section=self.section)

        if turn_on and not current_assignment:
            new_ssa = StudentSectionAssignment(student=student, section=self.section,
                    status=1, applied_time=datetime.now())
            new_ssa.save()
            msg = '%s applied for %s.' % (student.name, self.section)
            messages.add_message(self.request, messages.INFO, msg)
            log.info('%s: %s', self.request.user, msg)
        elif current_assignment and not turn_on:
            current_assignment.delete()
            msg = '%s unenrolled from %s.' % (student.name, self.section)
            messages.add_message(self.request, messages.INFO, msg)
            log.info('%s: %s', self.request.user, msg)
