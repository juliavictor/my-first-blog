"""
Django settings for mysite project.

Generated by 'django-admin startproject' using Django 1.11.10.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'k=c(7!%4h20!ui8y(=p5bfb#5v(w3%%gm9yqmw#9yzd3f_^%@p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'juliavictor.pythonanywhere.com', 'opinionline.freshope.ru', 'localhost', 'opinionline.ru']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog',
    'social_django', # <--
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware', # <--
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',  # <--
                'social_django.context_processors.login_redirect',  # <--
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

AUTHENTICATION_BACKENDS = (
    # 'social_core.backends.github.GithubOAuth2',
    'social_core.backends.twitter.TwitterOAuth',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.vk.VKOAuth2',
    'social_core.backends.google.GoogleOpenId',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.odnoklassniki.OdnoklassnikiOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_TWITTER_KEY = 'hrmQprTyhsytpQJtCbCeG7qnJ'
SOCIAL_AUTH_TWITTER_SECRET = 'kirMd8VvE5DF3Gc8r4mmD67no3YNn9Cilkbdlps9KLI3G9UuoD'

SOCIAL_AUTH_FACEBOOK_KEY = '949463291895207'  # App ID
SOCIAL_AUTH_FACEBOOK_SECRET = '78d3a81b22b67922018a1c9544ecd3fa'  # App Secret

SOCIAL_AUTH_VK_OAUTH2_KEY = '6429422'
SOCIAL_AUTH_VK_OAUTH2_SECRET = 'Gz7QUw5Geybe0tv9zzzo'
SOCIAL_AUTH_LOGIN_URL = '/app/oauth2login'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY ='585191437124-gdf3ntom9pg9n84ehhp8t2b4esbg5668'  #Paste CLient Key
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'V7YAVlfREYVyQ7I0NwIMuOdW' #Paste Secret Key

SOCIAL_AUTH_ODNOKLASSNIKI_OAUTH2_KEY = '1264920320'
SOCIAL_AUTH_ODNOKLASSNIKI_OAUTH2_SECRET = '71ED741FB49931BF36367332'
SOCIAL_AUTH_ODNOKLASSNIKI_OAUTH2_PUBLIC_NAME = 'CBAICGGMEBABABABA'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGIN_REDIRECT_URL = '/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Images
MEDIA_ROOT = (
os.path.join(BASE_DIR, 'images')
)

MEDIA_URL = '/media/'