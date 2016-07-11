from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from .models import Course, Section, Parent
from .forms import AuthenticationForm


class ScheduledCourse(object):
    def __init__(self, name, url, sections):
        self.name = name
        self.url = url
        self.sections = sections

    def __str__(self, *args, **kwargs):
        return self.name + ' ' + self.description


class Index(View):
    def get(self, request):
        return render(request, 'app/index.html')


def courses(request):
    sections = Section.objects.order_by('start_time')
    scheduled_courses = set((s.course for s in sections))
    scheduled_courses = [ScheduledCourse(c.name, c.url,
        [s for s in sections if s.course == c]) for c in Course.objects.order_by('name') if c in scheduled_courses]

    return render(request, 'app/courses.html', {'courses': scheduled_courses})


@login_required
def students(request):
    parents = Parent.objects.order_by('name')
    return render(request, 'app/students.html', {'parents': parents})


@login_required
def proposals(request):
    sections = Section.objects.filter(start_time__gt=datetime.now(),
        scheduled_status__in=(1, 2, 3)).order_by('start_time')
    return render(request, 'app/proposals.html', {'sections': sections})


class Login(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'app/login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.user_cache)
            return redirect('/app/')
        else:
            return render(request, 'app/login.html', {'form': form})
