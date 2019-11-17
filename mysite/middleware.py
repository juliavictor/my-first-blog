from social_django.middleware import SocialAuthExceptionMiddleware
from social_core import exceptions as social_exceptions
from django.shortcuts import HttpResponse
from django.shortcuts import render, redirect
from social.exceptions import AuthCanceled
import sqlite3
from django import db


class SocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        if type(exception) == AuthCanceled:
            return redirect('post_list')

        if type(exception) == sqlite3.OperationalError:
            if "database is locked" in str(exception):
                print("Error catched: database was locked")
                db.connections.close_all()
                print("Database connections all released...")
                return redirect('post_list')

            else:
                raise exception

        else:
            raise exception