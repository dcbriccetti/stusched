# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-12 01:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0022_parent_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='private_notes',
            field=models.TextField(blank=True),
        ),
    ]