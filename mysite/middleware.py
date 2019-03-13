from social_django.middleware import SocialAuthExceptionMiddleware
from social_core import exceptions as social_exceptions
from django.shortcuts import HttpResponse
from django.shortcuts import render, redirect
from social.exceptions import AuthCanceled

class SocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        if type(exception) == AuthCanceled:
            return redirect('post_list')
        else:
            raise exception