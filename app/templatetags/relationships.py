from django.template import Library
register = Library()


@register.filter
def students_intersection(s1, s2):
    common = set(s1) & set(s2)
    return ', '.join(sorted((s.name for s in common)))
