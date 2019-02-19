from django.contrib import admin
from .models import Post, Comment, Poll, Quote, PostAdmin, QuoteAdmin

admin.site.register(Post, PostAdmin)
admin.site.register(Comment)
admin.site.register(Poll)
admin.site.register(Quote, QuoteAdmin)





