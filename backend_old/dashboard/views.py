from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import *
from django.conf import settings

# Create your views here.
from shopify_store.shopify import *
from users.mixins import AdminLoginRequired


class DashboardHomePage(AdminLoginRequired, TemplateView):
    permission_required = True
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super(DashboardHomePage, self).get_context_data(**kwargs)
        context['title'] = 'Dashboard'
        return context


def json_product_list(request):
    products = get_products()
    json_data = products[0].to_dict()
    return JsonResponse(json_data)


class ShopifyProductList(AdminLoginRequired, TemplateView):
    template_name = 'dashboard/shopify/products.html'

    def get_context_data(self, **kwargs):
        context = super(ShopifyProductList, self).get_context_data(**kwargs)
        products = get_products()
        context['products'] = products
        return context


def product_3d_viewer(request, product_id):
    import base64
    # import requests
    # url = "https://www.pinclipart.com/picdir/middle/523-5232827_fingerprint-png-download-transparent-background-fingerprint-clipart.png"
    # # url = "https://www.pngitem.com/pimgs/m/138-1388188_finger-print-png-transparent-background-fingerprint-png-png.png"
    from django.contrib.staticfiles import finders
    file_path = finders.find('img/fingerprint.png')
    file_base64 = None
    with open(file_path, "rb") as image_file:
        read_file = image_file.read()
        file_base64 = base64.b64encode(read_file).decode('utf-8')
    data = {
        'file_base64': 'data:image/png;base64,' + file_base64
    }
    return render(request, 'dashboard/3DViewer/viewer.html', data)
