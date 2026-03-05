from django.core import serializers
from django.conf import settings
import shopify


shop_url = "https://%s:%s@%s.myshopify.com/admin/api/%s" % (
    settings.SHOPIFY_ADMIN_API_KEY, settings.SHOPIFY_ADMIN_API_PASSWORD, settings.SHOPIFY_SUBDOMAIN,
    settings.SHOPIFY_API_VERSION
)

shopify.ShopifyResource.set_site(shop_url)

# session = shopify.Session(settings.SHOPIFY_DOMAIN, '2020-04', settings.token)
# session_setup = shopify.Session.setup(api_key=settings.SHOPIFY_API_KEY, secret=settings.SHOPIFY_APP_SECRET)


def get_products():
    product = shopify.Product.find()
    # return serializers.serialize('json', product)
    return product


def total_products():
    count = shopify.Product.count()
    # shopify.Shop.current()
    return count
