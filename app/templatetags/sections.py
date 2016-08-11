from django.template import Library
from app.sections import SectionRows
register = Library()


@register.filter
def rows(student, user):
    return SectionRows(student.sections.all(), user)
