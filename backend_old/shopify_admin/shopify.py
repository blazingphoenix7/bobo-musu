import requests
from django.core import serializers

from bobo_musu_3479.shopify import *
import json

# shop_url = "https://%s:%s@%s.myshopify.com/admin/api/%s" % (
#     SHOPIFY_ADMIN_API_KEY, SHOPIFY_ADMIN_API_PASSWORD, settings.SHOPIFY_SUBDOMAIN, settings.SHOPIFY_API_VERSION
# )

# shopify.ShopifyResource.set_site(shop_url)

# session = shopify.Session(settings.SHOPIFY_DOMAIN, '2020-04', settings.token)
# session_setup = shopify.Session.setup(api_key=settings.SHOPIFY_API_KEY, secret=settings.SHOPIFY_APP_SECRET)


def current_shop():
    shop = shopify.Shop.current()
    return shop


def get_products():
    product = shopify.Product.find(limit=3)
    # return serializers.serialize('json', product)
    return product


def total_products():
    count = shopify.Product.count()
    # shopify.Shop.current()
    return count


def shopify_customers():
    customers = shopify.Customer.find(3163899363391)
    # return serializers.serialize('json', customers)
    return customers.to_dict()
