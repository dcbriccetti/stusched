# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-06 15:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0043_auto_20160728_2237'),
    ]

    operations = [
        migrations.RenameField(
            model_name='studentsectionassignment',
            old_name='changed',
            new_name='applied_time',
        ),
    ]
