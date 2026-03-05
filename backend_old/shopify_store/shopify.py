from django.core import serializers
from django.conf import settings
import shopify as admin_shopify
import json

# shop_url = "https://%s:%s@%s.myshopify.com/admin/api/%s" % (
#     settings.SHOPIFY_API_KEY, settings.SHOPIFY_APP_PASSWORD, settings.SHOPIFY_SUBDOMAIN, settings.SHOPIFY_API_VERSION
# )

shop_url = settings.SHOPIFY_ADMIN_API_URL

admin_shopify.ShopifyResource.set_site(shop_url)


# session = shopify.Session(settings.SHOPIFY_DOMAIN, '2020-04', settings.token)
# session_setup = shopify.Session.setup(api_key=settings.SHOPIFY_API_KEY, secret=settings.SHOPIFY_APP_SECRET)


def get_products():
    product = admin_shopify.Product.find()
    # return serializers.serialize('json', product)
    return product


def total_products():
    count = admin_shopify.Product.count()
    # shopify.Shop.current()
    return count


def shopify_customers():
    customers = admin_shopify.Customer.find(3163899363391)
    # return serializers.serialize('json', customers)
    return customers.to_dict()


def get_products_by_collection(collection_id):
    # collections = admin_shopify.Product.collections(id=collection_id)
    # print(collections.__dict__)
    return None


def collection_detail(collection_id):
    collection = admin_shopify.Product.find()
    print(collection)


def get_products_by_ids(product_ids):
    id_str_list = ','.join(str(x) for x in product_ids)
    products = admin_shopify.ProductListing.product_ids(product_ids=id_str_list)
    print(products)
    return products
