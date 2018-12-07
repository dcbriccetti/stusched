from django.urls import path
from . import adminviews, views

urlpatterns = [
    path('',          views.Index.as_view(),      name='index'),
    path('login',     views.Login.as_view(),      name='log-in'),
    path('logout',    views.logOut,               name='log-out'),
    path('courses',   views.Courses.as_view(),    name='courses'),
    path('admin',     adminviews.Admin.as_view(), name='admin'),
    path('news',      views.NewsView.as_view(),   name='news'),
    path('parent',    views.ParentView.as_view(), name='parent'),
    path('student',   views.Student.as_view()),
    path('student/<int:student_id>', views.Student.as_view(), name='student'),
    path('students',  views.students,             name='students'),
    path('section/<int:section_id>', views.section,       name='section'),
    path('section/<int:section_id>/register', views.Register.as_view(), name='register'),
    path('section/<int:section_id>/register/<int:student_id>', views.Register.as_view(), name='register-student'),
    path('section/<int:section_id>/calendar', views.Calendar.as_view(), name='calendar'),
    path('sections',  views.sections,             name='sections'),
]
