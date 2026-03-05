"""bobo_musu_3479 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="BOBO & Musu API",
        default_version='v1',
        description="API documentation",
        terms_of_service="",
        contact=openapi.Contact(email="borhan@crowdbotics.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('api_docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('', include('home.urls')),
    path('accounts/', include('allauth.urls')),
    path('api/v1/', include('home.api.v1.urls')),
    path('api/v1/', include('shopify_store.api.v1.urls')),
    # path('shopifyapp/', include('shopify_app.urls')),
    path('shopifyadmin/', include('shopify_admin.urls')),
    path('admin/', admin.site.urls),
    path('admin/dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('shopify-store/', include('shopify_store.urls')),
]

admin.site.site_header = 'Bobo & Musu'
admin.site.site_title = 'Bobo & Musu Admin Portal'
admin.site.index_title = 'Bobo & Musu Admin'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
