# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-07-31 20:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('values', '0012_auto_20170606_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='value',
            name='string_value_corrected',
            field=models.TextField(help_text='The string value or string representation of this value corrected by Bing Spell Checker', null=True),
        ),
    ]
