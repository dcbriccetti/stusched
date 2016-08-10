'Business logic relating to course sections'

from datetime import timedelta, datetime
from itertools import groupby
from app.students import students_of_parent


def get_viewable_section_ids(user):
    '''Return a set of the IDs of sections that the logged-in user may view.

    Parents may view any section in which at least one of their children have been accepted.'''

    from app.models import SS_STATUS_ACCEPTED, StudentSectionAssignment
    viewable_section_ids = set()
    if user and not user.is_staff:
        for student in students_of_parent(user):
            for section in student.sections.all():
                if StudentSectionAssignment.objects.filter(student=student, section=section,
                        status=SS_STATUS_ACCEPTED).count():
                    viewable_section_ids.add(section.id)
    return viewable_section_ids


def section_rows(sections, user=None):
    'Return a SectionRows object with future and past SectionRows'

    def make_section_rows(sections, user):
        sop = students_of_parent(user) if user else []

        class SectionRow:
            def __init__(self, section, viewable):
                self.section = section
                self.viewable = viewable

                def status_group_names():
                    from app.models import augmented_student_section_assignments
                    from app.models import SS_STATUSES_BY_ID, SS_STATUS_ACCEPTED
                    aug_ssas = augmented_student_section_assignments(section.id)
                    def status_from_assa(assa): return assa.ssa.status
                    aug_ssas.sort(key=status_from_assa)
                    num_statuses = len(set((assa.ssa.status for assa in aug_ssas)))

                    for status_id, grouped_assas in groupby(aug_ssas, status_from_assa):
                        def fmt_name(assa):
                            return assa.ssa.student.name + (' (waitlist)' if assa.waitlisted else '')
                        names = [fmt_name(assa) for assa in grouped_assas if not user or user.is_staff or assa.ssa.student in sop]
                        if names:
                            names.sort()
                            status_heading = '%s: ' % SS_STATUSES_BY_ID[status_id] if \
                                num_statuses > 1 or status_id != SS_STATUS_ACCEPTED else ''
                            yield '%s%s' % (status_heading, ', '.join(names))

                self.students = ', '.join(status_group_names())

        viewable_section_ids = get_viewable_section_ids(user)
        return [SectionRow(section, section.id in viewable_section_ids) for section in sections]

    class SectionRows:
        def __init__(self, future_sections, past_sections, user=user):
            self.future = make_section_rows(future_sections, user)
            self.past   = make_section_rows(past_sections,   user)

    def is_future(s):
        return s.start_time + timedelta(days=s.num_days) > datetime.now()

    def is_past(s):
        return not is_future(s)

    def section_time(s):
        return s.start_time

    future_sections = sorted(filter(is_future, sections), key=section_time)
    past_sections   = sorted(filter(is_past,   sections), key=section_time, reverse=True)

    return SectionRows(future_sections, past_sections)
