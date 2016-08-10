from django.conf.urls import url
from . import adminviews, views

urlpatterns = [
    url(r'^$',          views.Index.as_view(),      name='index'),
    url(r'^login$',     views.Login.as_view(),      name='login'),
    url(r'^logout$',    views.logOut,               name='log_out'),
    url(r'^courses$',   views.Courses.as_view(),    name='courses'),
    url(r'^admin$',         adminviews.Admin.as_view(),      name='admin'),
    url(r'^admin/email$',   adminviews.AdminEmail.as_view(), name='admin-email'),
    url(r'^parent$',    views.ParentView.as_view(), name='parent'),
    url(r'^student$',   views.Student.as_view()),
    url(r'^student/(?P<student_id>[0-9]+)$', views.Student.as_view(), name='student'),
    url(r'^students$',  views.students,             name='students'),
    url(r'^section/([0-9]+)$', views.section,       name='section'),
    url(r'^section/([0-9]+)/register$', views.Register.as_view(), name='register'),
    url(r'^section/([0-9]+)/register/([0-9]+)$', views.Register.as_view(), name='register-student'),
    url(r'^section/([0-9]+)/calendar$', views.Calendar.as_view(), name='calendar'),
    url(r'^sections$',  views.sections,             name='sections'),
]
