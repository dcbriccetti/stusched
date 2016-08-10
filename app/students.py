

def students_of_parent(user):
    from .models import Parent
    stus = []
    if user.is_active and not user.is_staff:  # Skip for anonymous or staff user
        parents = Parent.objects.filter(users=user)
        for p in parents:
            stus += p.students_sorted()
    stus.sort(key=lambda s: s.name)
    return stus


