#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from django import forms

STATUS_CHOICES = (
    (1, ("Язык и речь")),
    (2, ("Растения и животные")),
    (3, ("Культура и искусство")),
    (4, ("Химия и биология")),
    (5, ("Логика и восприятие")),
    (6, ("Земля и Вселенная")),
    (7, ("Человек и общество")),
    (8, ("Наука и технологии")),
    (9, ("История и археология")),
    (10, ("Медицина и здоровье"))
)

class Post(models.Model):
    author = models.ForeignKey('auth.User')
    title = models.CharField(max_length=200)
    text = models.TextField()
    tag = models.IntegerField(choices=STATUS_CHOICES, default=1)
    created_date = models.DateTimeField(
            default=timezone.now)
    published_date = models.DateTimeField(
            blank=True, null=True)
    image = models.ImageField(upload_to='img', default="default-image.png")

    def approved_comments(self):
        return self.comments.filter(approved_comment=True)


    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey('blog.Post', related_name='comments')
    author = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    approved_comment = models.BooleanField(default=False)

    def approve(self):
        self.approved_comment = True
        self.save()


    def __str__(self):
        return self.text

