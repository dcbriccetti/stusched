from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import View
from .models import Course, Section, Parent
from .models import Student as StudentModel
from .forms import AuthenticationForm, NewUserForm, StudentForm, ParentForm


class Index(View):
    def get(self, request):
        return render(request, 'app/index.html')


def courses(request):
    return render(request, 'app/courses.html', {'courses': Course.objects.filter(active=True).order_by('name')})


@login_required
def students(request):
    user = request.user
    if user.is_staff:
        parents = [p for p in Parent.objects.order_by('name') if p.active()]
    else:
        parents = Parent.objects.filter(users=user)

    return render(request, 'app/students.html', {
        'parents': parents,
        'viewable_section_ids': viewable_section_ids(request),
    })


def students_of_parent(user):
    stus = []
    if user.is_active:  # Skip for anonymous user
        parents = Parent.objects.filter(users=user)
        for p in parents:
            stus += p.student_set.all()
    return stus


def parent_of_one_of_these_students(user, students):
    stus = students_of_parent(user)
    return bool(set(stus) & set(students))


def sections(request):
    include_all = request.GET.get('include', 'future') == 'all'
    sections = Section.objects
    if not include_all:
        sections = sections.filter(start_time__gt=datetime.now())
    return render(request, 'app/sections.html', {
        'sections':             sections.order_by('start_time'),
        'viewable_section_ids': viewable_section_ids(request),
        'include_all':          include_all
    })


def viewable_section_ids(request):
    viewable_section_ids = set()
    if request.user and not request.user.is_staff:
        for stu in students_of_parent(request.user):
            for section in stu.sections.all():
                viewable_section_ids.add(section.id)
    return viewable_section_ids


def _these_students_in_other_sections(section_id, students):
    these_students_in_other_sections = {}  # section -> list of student names

    for student in students:
        other_sections_with_student = student.sections.exclude(id=section_id)

        for section_with_student in other_sections_with_student:
            student_names = these_students_in_other_sections.get(section_with_student, [])
            student_names.append(student.name)
            these_students_in_other_sections[section_with_student] = student_names

    return these_students_in_other_sections


@login_required
def section(request, section_id):
    section = Section.objects.get(id=int(section_id))
    students_in_this_section = section.student_set.all().order_by('name')

    ok_to_show = request.user.is_staff or parent_of_one_of_these_students(request.user, students_in_this_section)

    these_students_in_other_sections = _these_students_in_other_sections(section.id, students_in_this_section)

    class StudentsInSection:
        def __init__(self, section, student_names):
            self.section = section
            self.student_names = ', '.join(sorted(student_names))

    students_in_sections = [StudentsInSection(section, student_names)
        for section, student_names in these_students_in_other_sections.items() if len(student_names) > 1]
    students_in_sections.sort(key=lambda ss: ss.section.start_time)

    return render(request, 'app/section.html',
        {'section': section, 'students': students_in_this_section, 'overlaps': students_in_sections,
         'ok_to_show': ok_to_show})


class Login(View):
    def get(self, request):
        form = AuthenticationForm()
        data = {}
        for name in ('name', 'email', 'parent_code'):
            v = request.GET.get(name)
            if v:
                data[name] = v
        new_user_form = NewUserForm(data) if data else NewUserForm()
        return render(request, 'app/login.html', {'form': form, 'new_user_form': new_user_form})

    def post(self, request):
        if 'name' in request.POST:
            form = NewUserForm(data=request.POST)
            if form.is_valid():
                cd = form.cleaned_data
                User.objects.create_user(cd['username'], cd['email'], cd['password'])
                user = authenticate(username=cd['username'], password=cd['password'])
                login(request, user)
                code = cd.get('parent_code')
                if code:
                    parent = Parent.objects.get(code=code)
                else:
                    parent = Parent(name=cd['name'], email=cd['email'])
                    parent.save()
                parent.users.add(user)
                return redirect('/app/')
            else:
                return render(request, 'app/login.html', {'form': AuthenticationForm(), 'new_user_form': form})
        else:
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                return redirect('/app/')
            else:
                return render(request, 'app/login.html', {'form': form, 'new_user_form': NewUserForm()})


def valid_parent(user):
    parents = Parent.objects.filter(users=user)
    return parents[0] if parents else None


class ParentView(LoginRequiredMixin, View):
    def get(self, request):
        parent = valid_parent(request.user)
        if not parent:
            return redirect('/app/')  # todo error

        return render(request, 'app/parent.html', {
            'form':       ParentForm(instance=parent),
            'parent_id':  parent.id,
        })

    def post(self, request):
        parent = valid_parent(request.user)
        if not parent:
            return redirect('/app/')  # todo error

        form = ParentForm(data=request.POST, instance=parent)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 'Parent information saved.')
            return redirect('/app/')
        else:
            return render(request, 'app/parent.html', {
                'form':         form,
                'parent_id':    parent.id
            })


class Student(LoginRequiredMixin, View):
    def get(self, request, id_str):
        if id_str == '0':
            parent = Parent.objects.filter(id=request.GET['parent_id']).first()
            if not parent:
                return redirect('/app/')  # todo error

            form = StudentForm()
            student_id = 0
        else:
            student_id = int(id_str)
            student = StudentModel.objects.filter(id=student_id).first()
            if not student:
                return redirect('/app/')  # todo error

            form = StudentForm(instance=student)
            parent = student.parent

        if self._student_ok(parent, request.user):
            return render(request, 'app/student.html', {
                'form':       form,
                'parent_id':  parent.id,
                'student_id': student_id,
            })
        else:
            return redirect('/app/')

    def post(self, request, id_str):
        if id_str == '0':
            parent = Parent.objects.filter(id=request.GET['parent_id']).first()
            student = None
            student_id = 0
        else:
            student_id = int(id_str)
            student = StudentModel.objects.filter(id=student_id).first()
            parent = student.parent
        if self._student_ok(parent, request.user):
            form = StudentForm(data=request.POST, instance=student)
            if form.is_valid():
                saved_student = form.save(commit=False)
                saved_student.parent = parent
                saved_student.save()
                form.save_m2m()
                messages.add_message(request, messages.INFO, 'Student information saved.')
            else:
                return render(request, 'app/student.html', {
                    'form':         form,
                    'student_id':   student_id,
                    'parent_id':    parent.id
                })

        return redirect('/app/students')

    @staticmethod
    def _student_ok(parent, user):
        return user.is_staff or user in parent.users.all()


def logOut(request):
    logout(request)
    messages.add_message(request, messages.INFO, 'You are logged out.')
    return redirect('/')
