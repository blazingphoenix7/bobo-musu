
from django.urls.conf import path
# from django_encrypted_filefield.constants import FETCH_URL_NAME

from .views import *

urlpatterns = [
    path('', home, name="home"),
]
