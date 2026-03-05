from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .app_views import *
from shopify_store.api.v1 import store_views

router = DefaultRouter()
# router.register(u'devices', viewsets.FCMCustomDeviceViewSet, base_name='user_devices')
urlpatterns = [
    path('', include(router.urls)),
    # frontend app urls
    # path('test_notification/', test_notification, name='test_notification'),

    # app api urls
    path('app/customer/login-verify/', CustomerLoginVerify.as_view(), name='customer_login_verify'),
    path('app/devices/add/', CustomerFCMDeviceAdd.as_view(), name='customer_fcm_device_add'),
    path('app/shopify/customers/', ShopifyCustomers.as_view(), name='shopify_customers'),
    path('app/shopify/customers/add-fingerprint/', ShopifyCustomerAddNewFingerPrint.as_view(),
         name='add_customer_fingerprint'),
    path('app/shopify/customers/fingerprints/', ShopifyCustomersFingerPrintList.as_view(),
         name='shopify_customers_fingerprint_list'),

    path('app/shopify/customers/fingerprints/<int:pk>/', ShopifyCustomerFingeprintDetail.as_view(),
         name='shopify_customers_fingerprint_detail'),

    # path('app/shopify/customers/fingerprints/<int:pk>/',
    #      ShopifyCustomersFingerPrintDestroy.as_view(),
    #      name='shopify_customers_fingerprint_delete'),

    # fingerprint request urls
    path('app/fingerprint-request/send-request/', FingerprintRequestCreateAPIView.as_view(),
         name='api_send_fingerprint_request'),
    path('app/fingerprint-request/list/<str:graphql_customer_id>/', FingerprintRequestListAPIView.as_view(),
         name='api_fingerprint_request_list'),

    # app wishlist urls
    path('app/shopify/wishlist/', CustomerWishlistCreateAPIView.as_view(), name='api_add_product_to_wishlist'),
    path('app/shopify/wishlist/<str:graphql_customer_id>/', CustomerWishlistListAPIView.as_view(),
         name='api_customer_wishlist'),
    path('app/shopify/wishlist/<str:graphql_customer_id>/<str:graphql_product_id>/',
         CustomerWishlistDetailView.as_view(),
         name='api_customer_wishlist_detail'),

    path('app/shopify/sidebar-menu/', AppSidebarNavigationListAPIView.as_view(), name='api_sidebar_menu'),
    path('app/homepage-sliders/', AppHomepageSliderList.as_view(), name='api_homepage_slider_list'),
    path('app/homepage-banners/', AppHomepageBannerList.as_view(), name='api_homepage_banner_list'),
    path('app/shopify/collections/', AppCategoryListAPIView.as_view(), name='api_collection_list'),

    path('app/sidebar-filters/', AppSidebarFilterList.as_view()),
    path('app/customer-checkout-id/', APPCustomerCheckout.as_view()),
    path('app/customers/orders/', CustomerOrders.as_view()),
    path('app/customers/orders/<int:order_id>/', CustomerOrderDetails.as_view()),
    path('app/customers/orders/<int:order_id>/metafields/', OrderMetafields.as_view()),
    path('app/customers/orders/<int:order_id>/fulfillments/', OrderFulfillments.as_view()),
    path('app/customers/orders/<int:order_id>/fulfillments/<int:fulfillment_id>/', OrderFulfillmentDetails.as_view()),
    path('app/customers/orders/<int:order_id>/fulfillments/<int:fulfillment_id>/events/',
         OrderFulfillmentEvents.as_view()),
    # end app urls

    # shopify web urls
    path('web/shopify/customers/fingerprints/<int:customer_id>/', ShopifyCustomersFingerPrintListWeb.as_view(),
         name='api_web_shopify_customers_fingerprint_list'),

    path('web/shopify/customers/fingerprints/<int:customer_id>/<int:fingerprint_id>/',
         ShopifyCustomersFingerPrintDestroy.as_view(),
         name='api_web_shopify_customers_fingerprint_delete'),

    # fingerprint request urls for web
    path('web/fingerprint-request/send-request/', FingerprintRequestCreateAPIView.as_view(),
         name='api_web_api_send_fingerprint_request'),
    path('web/fingerprint-request/list/<int:customer_id>/', FingerprintRequestListAPIView.as_view(),
         name='api_web_api_fingerprint_request_list'),

    path('web/shopify/wishlist/', WebShopifyCustomerWishlistCreateAPIView.as_view(),
         name='api_web_add_product_to_wishlist'),
    path('web/shopify/wishlist-check/', web_wishlist_check,
         name='api_web_wishlist_check'),
    path('web/shopify/wishlist/<int:customer_id>/', CustomerWishlistListAPIView.as_view(),
         name='api_web_customer_wishlist'),
    path('web/shopify/wishlist/<int:customer_id>/<int:product_id>/',
         CustomerWishlistDetailView.as_view(),
         name='api_web_customer_wishlist_detail'),

    path('web/shopify/wishlist/<int:customer_id>/<int:product_id>/',
         CustomerWishlistDetailView.as_view(),
         name='api_web_customer_wishlist_destroy'),

    path('web/customer-registration/', store_views.ShopifyWebCustomerRegistration.as_view()),

    # store admin api_urls
    # path('api_url/', ShopifyProducts.as_view()),
    path('app/collections/<int:id>/', store_views.CollectionDetail.as_view()),
    path('app/collections/', store_views.CollectionList.as_view()),
    path('shopify/products/<slug:product_id>/3dmodel/', Product3DModelAPIView.as_view()),
]
