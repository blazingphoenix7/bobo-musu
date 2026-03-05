import datetime
import json

from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import ShopifyCustomerPermission
from .serializers import APPCustomerCheckoutIDSerializer
from ...functions import graphql_id_to_integer
from ...models import CustomerCheckoutID
from ...shopify_store_admin import *


class APPCustomerCheckout(APIView):
    permission_classes = [ShopifyCustomerPermission, ]
    serializer_class = APPCustomerCheckoutIDSerializer

    def get_object(self):
        try:
            data = CustomerCheckoutID.objects.get(customer_id=self.request.data.get('customer_id'))
            return data

        except CustomerCheckoutID.DoesNotExist:
            raise Http404

    def get(self, request):
        snippet = self.get_object()
        serializer = APPCustomerCheckoutIDSerializer(snippet)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            checkout = CustomerCheckoutID.objects.get(customer_id=self.request.data.get('customer_id'))
            checkout.checkout_id = request.data.get('checkout_id')
            checkout.save()
        except CustomerCheckoutID.DoesNotExist:
            checkout = CustomerCheckoutID(
                customer_id=request.data.get('customer_id'),
                graphql_customer_id=request.data.get('graphql_customer_id'),
            )
            checkout.checkout_id = request.data.get('checkout_id')
            checkout.save()
        serializer = APPCustomerCheckoutIDSerializer(checkout)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        CustomerCheckoutID.objects.filter(customer_id=self.request.data.get('customer_id')).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerOrders(APIView):
    permission_classes = [ShopifyCustomerPermission, ]

    @staticmethod
    def get(request, *args, **kwargs):
        customer_id = request.data['customer_id']
        limit = 10
        if request.GET.get('limit'):
            limit = request.GET.get('limit')
        page_info = None
        if request.GET.get('page_info'):
            page_info = request.GET.get('page_info')
        # print(page_info)
        orders = get_orders_by_customer(customer_id=customer_id, limit=int(limit), page_info=page_info)

        return Response(orders)


@api_view(['GET'])
def order_details(request, order_id):
    order = get_order_details(order_id)
    json_data = json.loads(order.to_json())
    return Response(json_data)


class CustomerOrderDetails(APIView):
    permission_classes = [ShopifyCustomerPermission, ]

    @staticmethod
    def get(request, **kwargs):
        # order_id = graphql_id_to_integer(kwargs['order_id'])
        order_id = kwargs['order_id']
        order = get_order_details_with_images(order_id, request.data['customer_id'])
        if order:
            return Response(order, status=status.HTTP_200_OK)

        return Response({'message': 'Nothing found'}, status=status.HTTP_404_NOT_FOUND)


class OrderMetafields(APIView):
    # permission_classes = [ShopifyCustomerPermission, ]

    @staticmethod
    def get(request, **kwargs):
        order_id = kwargs['order_id']
        metafields = get_order_metafields(order_id)
        # print(metafields.to_dict())

        if metafields:
            mt_arr = []
            for metafield in metafields:
                mt_arr.append(metafield.to_dict())
            return Response(mt_arr, status=status.HTTP_200_OK)

        return Response({'message': 'Nothing found'}, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def post(request, **kwargs):
        order_id = kwargs['order_id']
        post_data = {
            'key': request.data['key'],
            'value': request.data['value'],
            'value_type': request.data['value_type'],
            'namespace': request.data['namespace'],
            'description': request.data['description'],
        }
        metafields = add_order_metafield(order_id=order_id, metafield=post_data)
        if metafields:
            mt_arr = []
            for metafield in metafields:
                mt_arr.append(metafield.to_dict())
            return Response(mt_arr, status=status.HTTP_200_OK)

        return Response({'message': 'Failed to add metafields'}, status=status.HTTP_400_BAD_REQUEST)


class OrderFulfillments(APIView):
    permission_classes = [ShopifyCustomerPermission, ]

    @staticmethod
    def get(request, **kwargs):
        order_id = kwargs['order_id']
        try:
            events = order_fulfillments(order_id)
            if events:
                events_data = []
                for event in events:
                    events_data.append(event.to_dict())
                print(events_data)
                return Response(events_data)
        except Exception as e:
            print(str(e))
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class OrderFulfillmentDetails(APIView):
    permission_classes = [ShopifyCustomerPermission, ]

    @staticmethod
    def get(request, **kwargs):
        order_id = kwargs['order_id']
        fulfillment_id = kwargs['fulfillment_id']

        try:
            fulfillment = order_fulfillment_details(order_id, fulfillment_id)
            # return Response(events.to_dict())
            print(fulfillment.exists)
            if 'id' in fulfillment.to_dict():
                return Response(fulfillment.to_dict())
            else:
                return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(e)
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        # return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class OrderFulfillmentEvents(APIView):
    permission_classes = [ShopifyCustomerPermission, ]

    @staticmethod
    def get(request, **kwargs):
        order_id = kwargs['order_id']
        fulfillment_id = kwargs['fulfillment_id']
        try:

            events = order_fulfillment_events(order_id, fulfillment_id)
            print(events)
            return Response(events.json())
        except :
            return Response({'message': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
