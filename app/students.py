
def students_of_parent(user):
    from .models import Parent
    students = []
    if user and user.is_active and not user.is_staff:  # Skip for missing, anonymous or staff user
        for parent in Parent.objects.filter(users=user):
            students += parent.student_set.all()
    students.sort(key=lambda s: s.name)
    return students
