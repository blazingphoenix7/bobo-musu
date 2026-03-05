from django.conf import settings
from rest_framework import permissions

from shopify_store.functions import storefront_customer_data, graphql_id_to_integer


class ShopifyCustomerPermission(permissions.BasePermission):
    def has_permission(self, request, view):

        if type(request.data) is not dict:
            request.data._mutable = True

        if 'STOREFRONT-CUSTOMER-ACCESS-TOKEN' in request.headers:
            customer_access_token = request.headers['STOREFRONT-CUSTOMER-ACCESS-TOKEN']
            # graphql_customer_id = request.headers['CUSTOMER-ID']
            # print(customer_access_token)
            customer_data = storefront_customer_data(customer_access_token)
            # print(customer_data)
            if customer_data:
                request.data['graphql_customer_id'] = customer_data['id']
                customer_id = graphql_id_to_integer(customer_data['id'])
                request.data['customer_id'] = customer_id
                request.data['email'] = customer_data['email']
                # print(customer_data)
                return True
            else:
                return False

        else:
            return False


class CustomerFingerprintPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if type(request.data) is not dict:
            request.data._mutable = True
        if 'STOREFRONT-CUSTOMER-ACCESS-TOKEN' in request.headers:
            customer_access_token = request.headers['STOREFRONT-CUSTOMER-ACCESS-TOKEN']
            # print(customer_access_token)
            customer_data = storefront_customer_data(customer_access_token)
            if customer_data:
                print(customer_data)
                request.data['graphql_customer_id'] = customer_data['id']
                customer_id = graphql_id_to_integer(customer_data['id'])
                request.data['customer_id'] = customer_id
                # print(request.data)
                return True
            else:
                return False
        else:
            return False


class ShopifyCustomerWebPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        from urllib.parse import urlparse
        shopify_url = request.headers['Origin']
        parsed_url = urlparse(shopify_url)
        if parsed_url.hostname == settings.SHOPIFY_DOMAIN:
            return True
        return False

