# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-24 21:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_parent_notes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='description',
        ),
    ]
