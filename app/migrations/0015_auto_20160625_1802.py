# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-06-26 01:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_auto_20160624_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='section',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='course',
            name='url',
            field=models.URLField(blank=True),
        ),
    ]
