# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-02-18 10:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0030_auto_20180419_1345'),
    ]

    operations = [
        migrations.AddField(
            model_name='quote',
            name='source',
            field=models.TextField(default=''),
        ),
    ]