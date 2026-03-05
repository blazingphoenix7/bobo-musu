import datetime

import requests
import urllib.parse as urlparse
from urllib.parse import parse_qs
from django.core import serializers
from django.conf import settings
import shopify
import json

SHOPIFY_ADMIN_API_KEY = settings.SHOPIFY_ADMIN_API_KEY
SHOPIFY_ADMIN_API_PASSWORD = settings.SHOPIFY_ADMIN_API_PASSWORD
SHOPIFY_ADMIN_API_SECRET = settings.SHOPIFY_ADMIN_API_SECRET

shop_url = "https://%s:%s@%s.myshopify.com/admin/api/%s" % (
    SHOPIFY_ADMIN_API_KEY, SHOPIFY_ADMIN_API_PASSWORD, settings.SHOPIFY_SUBDOMAIN, settings.SHOPIFY_API_VERSION
)

shopify.ShopifyResource.set_site(shop_url)


def get_products_by_id_list(ids, fields):
    # url = '%s/products.json?ids=%s&fields=%s' % (shop_url, ids, fields)
    # # # return serializers.serialize('json', product)
    # response = requests.get(url)
    # #
    # return response.json()
    # shopify.ShopifyResource.clear_session()
    products = shopify.Product.find(ids={ids}, fields=fields)
    data = []
    for product in products:
        data.append(product.to_dict())
    return data


def create_checkout_without_line_items(email):
    url = "https://%s.myshopify.com/api/%s/graphql.json" % (settings.SHOPIFY_SUBDOMAIN, settings.SHOPIFY_API_VERSION)
    storefront_token = settings.SHOPIFY_STOREFRONT_ACCESS_TOKEN
    # print(storefront_token.encode().decode('ascii'))
    # encoded_storefront_token = base64.b64encode(storefront_token.encode()).decode('ascii')
    jaon_data = {
        "query": """
               mutation checkoutCreate($input: CheckoutCreateInput!) {
                  checkoutCreate(input: $input) {
                    checkout {
                      id
                    }
                    checkoutUserErrors {
                      code
                      field
                      message
                    }
                  }
                }
                """,
        "variables": {
            "input": {"email": email}
        }
    }

    headers = {
        'X-Shopify-Storefront-Access-Token': storefront_token.encode('idna').decode('utf-8'),
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, json=jaon_data)
    res_json = response.json()
    return res_json


def get_url_param_value(url, param):
    parsed = urlparse.urlparse(url)
    return parse_qs(parsed.query).get(param)[0]


def get_orders_by_customer(customer_id, limit=10, status='any', page_info=None):
    # orders = shopify.Order.find(customer_id=customer_id, limit=limit, status=status)
    orders = shopify.Order.find(customer_id=customer_id, limit=limit, status=status)
    if page_info is not None:
        page_url = "https://%s.myshopify.com/admin/api/%s/orders.json?limit=%s&page_info=%s" % (
            settings.SHOPIFY_SUBDOMAIN, settings.SHOPIFY_API_VERSION, limit, page_info)
        # print(page_url)
        orders = shopify.Order.find(from_=page_url)
    next_page = orders.has_next_page()
    prev_page = orders.has_previous_page()
    pagination = orders.metadata.get('pagination')
    next_page_info = None
    prev_page_info = None
    next_page_limit = None
    prev_page_limit = None
    if 'next' in pagination:
        next_page_info = get_url_param_value(url=pagination.get('next'), param='page_info')
        next_page_limit = get_url_param_value(url=pagination.get('next'), param='limit')
    if 'previous' in pagination:
        prev_page_info = get_url_param_value(url=pagination.get('previous'), param='page_info')
        prev_page_limit = get_url_param_value(url=pagination.get('previous'), param='limit')
    # print(pagination.get('next'))
    order_data = []
    product_ids = []
    for order in orders:
        line_items = order.to_dict()['line_items']
        for item in line_items:
            product_ids.append(item['product_id'])

        order_instance = order.to_dict()
        order_data.append(order_instance)
    str_ids = str(product_ids)[1:-1].replace(" ", "")
    product_images = get_products_by_id_list(str_ids, fields='id,images')
    # print(product_images)
    updated_order_data = []

    for order in orders:
        order_instance = order.to_dict()
        line_items = order_instance['line_items']
        updated_line_items = []
        for item in line_items:
            # images = {images['id'] == item['product_id']: images for images in product_images}
            # print(images)
            images = [images for images in product_images if images['id'] == item['product_id']][0]
            if images:
                item.update({'images': images['images']})
            # print(images)
            updated_line_items.append(item)
        order_instance['line_items'] = updated_line_items
        updated_order_data.append(order_instance)

    data = {
        'next_page': next_page,
        'prev_page': prev_page,
        'pagination': {
            'next_page_info': next_page_info,
            'prev_page_info': prev_page_info,
        },
        'orders': updated_order_data,
        # 'images': product_images,
    }
    return data


def get_order_details(order_id, customer_id):
    order = shopify.Order.find(order_id, customer_id=customer_id)
    return order.to_dict()


def get_order_details_with_images(order_id, customer_id):
    order = shopify.Order.find(order_id, customer_id=customer_id)

    product_ids = []
    for item in order.to_dict()['line_items']:
        product_ids.append(item['product_id'])

    str_ids = str(product_ids)[1:-1].replace(" ", "")
    product_images = get_products_by_id_list(str_ids, fields='id,images')

    updated_line_items = []
    for item in order.to_dict()['line_items']:
        # images = {images['id'] == item['product_id']: images for images in product_images}
        # print(images)
        images = [images for images in product_images if images['id'] == item['product_id']][0]
        if images:
            item.update({'images': images['images']})
        # print(images)
        updated_line_items.append(item)

    order_instance = order.to_dict()
    order_instance['line_items'] = updated_line_items
    return order_instance


def get_order_metafields(order_id):
    order = shopify.Order.find(order_id)
    metafields = order.metafields()
    print(metafields)
    return metafields


def add_order_metafield(order_id, metafield):
    order = shopify.Order.find(order_id)
    print(metafield)
    post_data = {
        'key': 'delivery_date',
        'value': datetime.date.today(),
        'value_type': 'string',
        'namespace': 'delivery'
    }
    order.add_metafield(shopify.Metafield(metafield))
    # order.save()
    return order.metafields()


def order_fulfillments(order_id):
    return shopify.Fulfillment().find(order_id=order_id)


def order_fulfillment_details(order_id, fulfillment_id):
    return shopify.Fulfillment.find(fulfillment_id, order_id=order_id)


def order_fulfillment_events(order_id, fulfillment_id):
    site_url = f'{shop_url}/orders/{order_id}/fulfillments/{fulfillment_id}/events.json'
    print(site_url)
    response = requests.get(site_url)
    return response
