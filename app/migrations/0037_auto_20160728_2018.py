# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-07-29 03:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0036_student_sections2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentsectionassignment',
            name='changed',
        ),
        migrations.RemoveField(
            model_name='studentsectionassignment',
            name='status',
        ),
    ]