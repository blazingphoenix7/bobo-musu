from django.urls import path
from .views_shopify_web import *


urlpatterns = [
    path('store/web/customer/<int:customer_id>/wishlist/', shopify_customer_wishlist),
]
