# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-17 05:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0030_parent_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='grade_from_age',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
