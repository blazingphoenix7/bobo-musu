import base64
import os
from urllib.parse import urlparse

from django.core.files.base import ContentFile
from django.http import *
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test

from django.shortcuts import render
from django.views.static import serve
from rest_framework import status
from rest_framework.response import Response

from shopify_admin.shopify import shopify
# Create your views here.
from requests import get

from shopify_store.functions import decrypt_file
from shopify_store.models import ShopifyCustomerFingerPrint


def shopify_admin_home(request):
    products = shopify.Product.find(limit=3)
    if products:
        data = {
            'title': 'Shopify Admin',
            'products': products
        }
        return render(request, 'shopify_admin/home.html', data)


def yts_movie_test(request):

    url = 'https://yts.mx/api/v2/list_movies.json'
    response = get(url)
    return render(request, 'shopify_admin/yts-test.html', response.json())


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def download_fingerprint_file(request, pk):
    if request.user.is_superuser:
        fingerprint_obj = ShopifyCustomerFingerPrint.objects.get(pk=pk)
        if fingerprint_obj:
            image = decrypt_file(fingerprint_obj.fingerprint_file)

            file_path = urlparse(fingerprint_obj.fingerprint_file.url)
            base_filename = os.path.basename(file_path.path)
            file_name = "%s_%s.png" % (fingerprint_obj.customer_id, base_filename)
            print(file_name)
            file_content = ContentFile(base64.b64decode(image))
            response = HttpResponse(file_content, content_type='image/png')
            response['Content-Disposition'] = 'attachment; filename=%s' % file_name
            return response

    return HttpResponseNotAllowed('Permission not allowed')
