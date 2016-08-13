import factory
from factory import Faker as Ff
from app.models import Parent, Student, Section
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User


class ParentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Parent

    name = Ff('name')
    email = Ff('safe_email')


class StudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Student

    name = Ff('name')
    birthdate = Ff('date_time')
    notes = Ff('sentences')


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Section

    start_time = '2016-08-30T13:00:00'
    scheduled_status = 1
    hours_per_day = 3
    num_days = 1


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    password = make_password('password')
    email = factory.Faker('safe_email')
