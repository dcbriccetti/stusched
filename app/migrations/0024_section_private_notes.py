# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-12 02:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0023_student_private_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='section',
            name='private_notes',
            field=models.TextField(blank=True),
        ),
    ]
