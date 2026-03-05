from django.urls import path, include

from shopify_store.views import *

urlpatterns = [
    path('', include('shopify_store.urls_shopify_web')),
    path('test-base64/', test_base64),
    path('render-data/', check_html_render),
]
