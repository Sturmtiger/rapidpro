# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2020-02-29 15:04
from __future__ import unicode_literals

from django.db import migrations
import temba.utils.models


class Migration(migrations.Migration):

    dependencies = [
        ('msgs', '0115_auto_20191125_1450'),
    ]

    operations = [
        migrations.AlterField(
            model_name='broadcast',
            name='text',
            field=temba.utils.models.TranslatableField(help_text='The localized versions of the message text', max_length=640, verbose_name='Translations'),
        ),
    ]