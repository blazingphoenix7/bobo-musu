from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ...shopify import *
from .serializers import ShopifyWebCustomerRegistrationSerializer


class ShopifyWebCustomerRegistration(APIView):

    @staticmethod
    def post(request):
        serializer = ShopifyWebCustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            customer = serializer.save()
            print(customer)
            if 'data' in customer and 'customerCreate' in customer['data']:
                if customer['data']['customerCreate'] is not None:
                    if customer['data']['customerCreate']['customer']:
                        return Response(customer, status=status.HTTP_201_CREATED)
                    return Response(customer['data']['customerCreate']['customerUserErrors'],
                                    status=status.HTTP_400_BAD_REQUEST)
                return Response(customer['errors'],
                                status=status.HTTP_400_BAD_REQUEST)

            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def check_api_url(request):
    return HttpResponse(settings.SHOPIFY_ADMIN_API_URL)


class ShopifyProducts(APIView):
    @staticmethod
    def get(request):
        products = shopify_customers()
        print(products)
        return JsonResponse(products)


class CollectionList(APIView):
    @staticmethod
    def get(request, *args, **kwargs):
        collections = admin_shopify.SmartCollection.find()
        print(collections)
        data_list = []
        for col in collections:
            data_list.append(col.to_dict())
        data = {
            'title': 'Title',
            'data': data_list
        }
        return Response(data_list, status=status.HTTP_200_OK)


class CollectionDetail(APIView):

    @staticmethod
    def get(request, *args, **kwargs):
        products = admin_shopify.Product.find(limit=2)
        print(products)
        list_product = []
        for product in products:
            list_product.append(product.__dict__)
        return JsonResponse(list_product, safe=False)
        # return Response(list(products))



