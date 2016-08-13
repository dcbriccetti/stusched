import factory
from app.models import Parent, Student
from faker import Faker
f = Faker()


class ParentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Parent

    name = f.name()
    email = f.email()


class StudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Student

    name = f.name()
    birthdate = f.date_time()
    notes = f.sentences()


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Student
