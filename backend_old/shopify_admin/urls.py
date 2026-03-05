from django.urls.conf import path
from . import views
urlpatterns = [
    path('', views.shopify_admin_home, name='shopify_admin_home'),
    path('yts-test/', views.yts_movie_test, name='yts_test'),
    path('download-fingerprint/<int:pk>/', views.download_fingerprint_file, name='download_fingerprint_file'),
]
