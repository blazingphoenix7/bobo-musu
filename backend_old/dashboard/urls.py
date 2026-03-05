from django.urls import path
from .views import *

app_name = 'dashboard'
urlpatterns = [
    path('', DashboardHomePage.as_view(), name='dashboard_home'),
    path('3dviews/products/<slug:product_id>/', product_3d_viewer, name='fingerprint_3d_viewer'),
    path('shopify/products/json/', json_product_list),
    path('shopify/products/', ShopifyProductList.as_view(), name='shopify_products'),
]
