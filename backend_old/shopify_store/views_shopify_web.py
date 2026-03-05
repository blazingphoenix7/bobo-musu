from django.http import JsonResponse
from django.shortcuts import render

from shopify_store.shopify_store_admin import get_products_by_id_list
from .models import *


def shopify_customer_wishlist(request, customer_id):
    product_ids = ShopifyCustomerWishList.objects.filter(
        customer_id=customer_id).values_list('product_id', flat=True).distinct()
    if product_ids:

        str_ids = ','.join(str(e) for e in product_ids)
        # print(str(str1))
        fields = 'id,title,handle,image'
        products = get_products_by_id_list(str_ids, fields)
        # print(products)
        # data = {
        #     'products': products,
        # }
        return render(request, 'store/customer_wishlist.html', {'products': products})
    return render(request, 'store/customer_wishlist.html', {'products': []})
    # return JsonResponse(products)
