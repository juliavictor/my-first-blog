from django.contrib import admin
from .models import Post, Comment, Poll

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Poll)
