
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from home.api.v1.viewsets import SignupViewSet, LoginViewSet, HomePageViewSet, CustomTextViewSet
from .views import *
router = DefaultRouter()
router.register('signup', SignupViewSet, basename='signup')
router.register('login', LoginViewSet, basename='login')
router.register('customtext', CustomTextViewSet)
router.register('homepage', HomePageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # path('webhook/cart/', cart_webhook),
    # path('shopify/products/', shopify_products),
    # path('shopify/products/<int:product_id>/', product_detail),
    # path('shopify/products/total/', api_total_products),
]
