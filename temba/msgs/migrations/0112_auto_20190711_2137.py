# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-07-12 00:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('msgs', '0111_auto_20171116_0922'),
    ]

    operations = [
        migrations.AlterField(
            model_name='broadcast',
            name='status',
            field=models.CharField(choices=[('I', 'Initializing'), ('P', 'Pending'), ('Q', 'Queued'), ('W', 'Wired'), ('S', 'Sent'), ('D', 'Delivered'), ('H', 'Handled'), ('E', 'Error Sending'), ('F', 'Failed Sending'), ('R', 'Resent message'), ('U', 'Undelivered'), ('A', 'Read')], default='I', help_text='The current status for this broadcast', max_length=1, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='msg',
            name='status',
            field=models.CharField(choices=[('I', 'Initializing'), ('P', 'Pending'), ('Q', 'Queued'), ('W', 'Wired'), ('S', 'Sent'), ('D', 'Delivered'), ('H', 'Handled'), ('E', 'Error Sending'), ('F', 'Failed Sending'), ('R', 'Resent message'), ('U', 'Undelivered'), ('A', 'Read')], db_index=True, default='P', help_text='The current status for this message', max_length=1, verbose_name='Status'),
        ),
    ]