from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import hmac
import hashlib
import base64
from home.api.v1.shopify import *


def get_hmac(body, secret):
    hash_code = hmac.new(secret.encode('utf-8'), body, hashlib.sha256)
    return base64.b64encode(hash_code.digest()).decode()


def hmac_is_valid(body, secret, hmac_to_verify):
    return get_hmac(body, secret) == hmac_to_verify


@csrf_exempt
@api_view(['POST'])
def cart_webhook(request):
    shopify_hmac = request.headers.get('X-Shopify-Hmac-Sha256')
    if hmac_is_valid(request.body, settings.SHOPIFY_WEBHOOK_SIGNED_KEY, shopify_hmac):
        print('valid')
        return Response(status=status.HTTP_200_OK)
    else:
        print('invalid')
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def shopify_products(request):
    products = shopify.Product.find()
    next_page = None
    if products.has_next_page():
        next_page = products.next_page()
    json_products = []
    if len(products) > 0:
        for product in products:
            json_products.append(product.to_dict())

    data = {
        'next_page': next_page,
        'products': json_products
    }

    return Response(data)


@api_view(['GET'])
def product_detail(request, product_id):
    product = shopify.Product.find(product_id)
    return Response(product.to_dict())


@api_view(['GET'])
def api_total_products(request):
    data = {
        # 'count': total_products,
        'total': total_products(),
    }
    return Response(data)
