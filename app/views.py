from datetime import datetime, timedelta
import logging
from itertools import groupby
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import View
from app.students import students_of_parent
from .models import Course, Section, Parent, SS_STATUSES_BY_ID, SS_STATUS_ACCEPTED, augmented_student_section_assignments, \
    StudentSectionAssignment
from .models import Student as StudentModel
from .forms import AuthenticationForm, NewUserForm, StudentForm, ParentForm

log = logging.getLogger(__name__)


class Index(View):
    def get(self, request):
        return render(request, 'app/index.html')


class Courses(View):
    def get(self, request):
        wci = 'wants_courses__id'
        wc = StudentModel.objects.values(wci).annotate(total=Count('id'))
        want_by_course = {e[wci]: e['total'] for e in wc if e[wci]}

        return render(request, 'app/courses.html', {
            'courses':          Course.objects.filter(active=True).order_by('name'),
            'want_by_course':   want_by_course,
            'student_wants':    get_student_wants(request.user),
        })

    def post(self, request):
        user = request.user
        wants_by_student = {csw.student: csw for csw in get_student_wants(user)}
        changed = False

        for student in students_of_parent(user):
            old_wants = wants_by_student[student].course_ids
            new_wants = set()
            # The checkbox names are in the form want-<student ID>-<course ID>
            for key_parts in (key.split('-') for key, _ in request.POST.items() if key.startswith('want-')):
                if int(key_parts[1]) == student.id:
                    new_wants.add(int(key_parts[2]))

            additions = new_wants - old_wants
            removals  = old_wants - new_wants

            for addition in additions:
                course = Course.objects.get(pk=addition)
                student.wants_courses.add(course)
                changed = True

            for removal in removals:
                course = Course.objects.get(pk=removal)
                student.wants_courses.remove(course)
                changed = True

        if changed:
            msg = 'Course interest settings saved.'
            messages.add_message(request, messages.INFO, msg)
            log.info('%s: %s', request.user, msg)

        return redirect(reverse('courses'))


@login_required
def students(request):
    user = request.user
    if user.is_staff:
        parents = [p for p in Parent.objects.order_by('name') if p.active()]
    else:
        parents = Parent.objects.filter(users=user)

    return render(request, 'app/students.html', {
        'parents': parents,
        'get_viewable_section_ids': get_viewable_section_ids(request.user),
    })


def parent_of_one_of_these_students(user, students):
    return bool(set(students_of_parent(user)) & set(students))


def get_student_wants(user):
    class StudentCourseWants:
        def __init__(self, student, course_ids):
            self.student = student
            self.course_ids = course_ids

    students = students_of_parent(user)
    return [StudentCourseWants(student, set((course.id for course in student.wants_courses.all())))
            for student in students]


def make_section_rows(user, sections):
    sop = students_of_parent(user) if user else []

    class SectionRow:
        def __init__(self, section, viewable):
            self.section = section
            self.viewable = viewable

            def status_group_names():
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


def sections(request):
    include_past_sections = request.GET.get('include', 'future') == 'all'
    sections = Section.objects.all().order_by('-start_time')
    def is_future(s): return s.start_time + timedelta(days=s.num_days) > datetime.now()
    future_sections = sorted(filter(is_future, sections), key=lambda s: s.start_time)
    past_sections   = filter(lambda s: not is_future(s), sections) if include_past_sections else []
    return render(request, 'app/sections.html', {
        'future_section_rows':      make_section_rows(request.user, future_sections),
        'past_section_rows':        make_section_rows(request.user, past_sections),
        'include_past_sections':    include_past_sections,
    })


def get_viewable_section_ids(user):
    viewable_section_ids = set()
    if user and not user.is_staff:
        for student in students_of_parent(user):
            for section in student.sections.all():
                if StudentSectionAssignment.objects.filter(student=student, section=section,
                        status=SS_STATUS_ACCEPTED).count():
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
    students_in_this_section = section.students_sorted()
    accepted_students_ids = set((ssa.student_id for ssa in StudentSectionAssignment.objects.
        filter(section_id=section_id, status=SS_STATUS_ACCEPTED)))
    accepted_students_in_this_section = [
        student for student in students_in_this_section if student.id in accepted_students_ids]

    ok_to_show_students = request.user.is_staff or \
        parent_of_one_of_these_students(request.user, accepted_students_in_this_section)

    these_students_in_other_sections = _these_students_in_other_sections(section.id, accepted_students_in_this_section)

    class StudentsInSection:
        def __init__(self, section, student_names):
            self.section = section
            self.student_names = ', '.join(sorted(student_names))

    students_in_sections = [StudentsInSection(section, student_names)
        for section, student_names in these_students_in_other_sections.items() if len(student_names) > 1]
    students_in_sections.sort(key=lambda ss: ss.section.start_time)

    return render(request, 'app/section.html', {
        'section':  section,
        'students': students_in_this_section,
        'overlaps': students_in_sections,
        'ok_to_show_students': ok_to_show_students
    })


class Login(View):
    def get(self, request):
        form = AuthenticationForm()
        data = {}
        for name in ('name', 'email', 'parent_code'):
            v = request.GET.get(name)
            if v:
                data[name] = v
        new_user_form = NewUserForm(data) if data else NewUserForm()
        return render(request, 'app/login.html', {
            'form':             form,
            'new_user_form':    new_user_form,
            'next':             request.GET.get('next', '')
        })

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
                log.info('%s %s created and logged in', user, parent.name)
                messages.add_message(request, messages.INFO, 'Account created')
                return redirect(request.POST.get('next') or '/app/')
            else:
                return render(request, 'app/login.html', {'form': AuthenticationForm(), 'new_user_form': form})
        else:
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                vp = valid_parent(request.user)
                log.info('%s %s logged in', request.user, vp.name if vp else '[No parent]')
                return redirect(request.POST.get('next') or '/app/')
            else:
                return render(request, 'app/login.html', {'form': form, 'new_user_form': NewUserForm()})


def logOut(request):
    name = request.user.username
    logout(request)
    messages.add_message(request, messages.INFO, 'You are logged out.')
    log.info('%s logged out', name)
    return redirect('/')


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
            msg = 'Parent information saved.'
            messages.add_message(request, messages.INFO, msg)
            log.info('%s %s %s', request.user, parent.name, msg)
            return redirect('/app/')
        else:
            return render(request, 'app/parent.html', {
                'form':         form,
                'parent_id':    parent.id
            })


class Student(LoginRequiredMixin, View):
    def get(self, request, student_id):
        if student_id == '0':
            parent = get_object_or_404(Parent, pk=request.GET['parent_id'])
            form = StudentForm()
            student_id = 0
        else:
            student = get_object_or_404(StudentModel, pk=student_id)
            form = StudentForm(instance=student)
            parent = student.parent

        if self._student_ok(parent, request.user):
            return render(request, 'app/student.html', {
                'form':       form,
                'parent_id':  parent.id,
                'student_id': student_id,
            })
        else:
            raise Http404('That is not a student you can edit')

    def post(self, request, student_id):
        if student_id == '0':
            parent = Parent.objects.filter(id=request.GET['parent_id']).first()
            student = None
        else:
            student = StudentModel.objects.filter(id=student_id).first()
            parent = student.parent
        if self._student_ok(parent, request.user):
            form = StudentForm(data=request.POST, instance=student)
            if form.is_valid():
                saved_student = form.save(commit=False)
                saved_student.parent = parent
                saved_student.save()
                form.save_m2m()
                msg = 'Student information saved.'
                messages.add_message(request, messages.INFO, msg)
                log.info('%s %s: %s %s', request.user, parent.name, saved_student.name, msg)
            else:
                return render(request, 'app/student.html', {
                    'form':         form,
                    'student_id':   student_id,
                    'parent_id':    parent.id
                })
        else:
            raise Http404('That is not a student you can edit')

        return redirect('/app/students')

    @staticmethod
    def _student_ok(parent, user):
        return user.is_staff or user in parent.users.all()


class Register(LoginRequiredMixin, View):
    def get(self, request, section_id):
        from app.reg import RegistrationSetter
        rs = RegistrationSetter(request, section_id)

        return render(request, 'app/section_reg.html', {
            'section':                  rs.section,
            'students_with_assignment': rs.swas,
        })

    def post(self, request, section_id, student_id):
        from app.reg import RegistrationSetter
        student = get_object_or_404(StudentModel, pk=student_id)
        if parent_of_one_of_these_students(request.user, [student]):
            apply    = 'apply'    in request.POST
            unenroll = 'unenroll' in request.POST
            if apply or unenroll:
                rs = RegistrationSetter(request, section_id)
                rs.set(student, apply)

        return redirect('/app/section/%s/register' % section_id)


class Calendar(View):
    def get(self, request, section_id):
        section = Section.objects.filter(pk=section_id).first()
        response = render(request, "app/event.ics", {
            'section': section,
        }, content_type="text/icalendar")
        response['Content-Disposition'] = 'attachment; filename="event.ics"'
        return response
