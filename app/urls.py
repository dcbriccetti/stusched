from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$',          views.Index.as_view(),      name='index'),
    url(r'^login$',     views.Login.as_view(),      name='login'),
    url(r'^logout$',    views.logOut,               name='log_out'),
    url(r'^courses$',   views.Courses.as_view(),    name='courses'),
    url(r'^parent$',    views.ParentView.as_view(), name='parent'),
    url(r'^student$',   views.Student.as_view()),
    url(r'^student/([0-9]+)$', views.Student.as_view()),
    url(r'^section/([0-9]+)$', views.section,       name='section'),
    url(r'^section/([0-9]+)/register$', views.Register.as_view(), name='register'),
    url(r'^students$',  views.students,             name='students'),
    url(r'^sections$',  views.sections,             name='sections'),
]
