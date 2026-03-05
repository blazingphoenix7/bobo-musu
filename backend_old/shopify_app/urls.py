from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login, name='shopify_app_login'),
    path('authenticate/', views.authenticate, name='shopify_app_authenticate'),
    path('finalize/', views.finalize, name='shopify_app_login_finalize'),
    path('logout/', views.logout, name='shopify_app_logout'),

    # app links
    path('', views.app_home_page, name='root_path'),
    path('boboandmusu/', views.boboandmusu_store_view, name="boboandmusu"),
    path('web/', views.boboandmusu_store_view, name="app_web"),
    path('web/api/', views.boboandmusu_store_view, name="app_web"),
    path('fingerprints/', views.AppFingerprintList.as_view(), name='app_fingerprint_list'),
]
