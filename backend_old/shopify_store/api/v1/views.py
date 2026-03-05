import urllib.request

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import *
from rest_framework.response import Response
from rest_framework.views import APIView

from shopify_store.shopify import *
from .permissions import ShopifyCustomerPermission, ShopifyCustomerWebPermissions
from .serializers import *
from ...functions import integer_to_graphpql_customer

from ...shopify import admin_shopify
from ...shopify_store_admin import get_products_by_id_list


class ShopifyCustomers(APIView):

    @staticmethod
    def get(request):
        print(shopify_customers())
        data = {
            'customers': shopify_customers()
        }
        return Response(
            data, status=status.HTTP_200_OK
        )


class CustomerLoginVerify(APIView):
    @staticmethod
    def get(request):
        access_token = request.headers['STOREFRONT-CUSTOMER-ACCESS-TOKEN']
        url = "https://%s.myshopify.com/api/%s/graphql.json" % (
            settings.SHOPIFY_SUBDOMAIN, settings.SHOPIFY_API_VERSION)
        storefront_token = settings.SHOPIFY_STOREFRONT_ACCESS_TOKEN
        query = '''
                query
                    {
                        customer(customerAccessToken: "%s") {
                            id
                            lastName
                            firstName
                            email
                        }
                    }
                ''' % access_token

        headers = {
            'X-Shopify-Storefront-Access-Token': storefront_token.encode('idna').decode('utf-8'),
            'Content-Type': 'application/json',
        }

        # response = requests.request("POST", url, headers=headers, json={'query': query})
        values = {'query': query}
        data = json.dumps(values).encode('utf-8')
        # response = urllib.request.Request(url, data, headers)
        req = urllib.request.Request(url, data, headers)
        with urllib.request.urlopen(req) as f:
            res = f.read()

        res_json = json.loads(res.decode())

        # print(res_json['data']['customer'])
        if res_json['data']['customer'] is not None:
            # print(res_json['data']['customer'])
            # return res_json['data']['customer']
            return Response(res_json['data']['customer'])
        else:
            return Response(res_json)


class CustomerFCMDeviceAdd(CreateAPIView):
    permission_classes = [ShopifyCustomerPermission, ]
    serializer_class = ShopifyCustomerFCMDeviceSerializer

    # def perform_create(self, serializer):
    #     graphql_customer_id = self.request.data.get('graphql_customer_id')
    #     serializer.save(graphql_customer_id=graphql_customer_id)

    def create(self, request, *args, **kwargs):
        registration_id = request.data.get('registration_id')
        graphql_customer_id = request.data.get('graphql_customer_id')
        queryset = ShopifyCustomerFCMDevice.objects.filter(registration_id=registration_id,
                                                           graphql_customer_id=graphql_customer_id)
        if queryset.exists():
            data = {
                "message": "This token already exist for this user",
                "success": False

            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return super(CustomerFCMDeviceAdd, self).create(request, *args, **kwargs)


class ShopifyCustomerAddNewFingerPrint(CreateAPIView):
    serializer_class = ShopifyCustomerFingerPrintSerializer
    permission_classes = [ShopifyCustomerPermission, ]

    # def perform_create(self, serializer):
    #     # graphql_customer_id = self.request.data.get('graphql_customer_id')
    #
    #     customer_access_token = self.request.headers['STOREFRONT-CUSTOMER-ACCESS-TOKEN']
    #     customer = storefront_customer_data(customer_access_token)
    #     customer_id = graphql_id_to_integer(customer['id'])
    #     serializer.save(
    #         graphql_customer_id=customer['id'],
    #         customer_id=customer_id,
    #     )

    def create(self, request, *args, **kwargs):
        # request.data['customer_id'] = kwargs['customer_id']

        # print(customer['id'])
        # _mutable = request.data._mutable
        # request.data._mutable = True
        # # graphql_customer_id = request.data.get('graphql_customer_id')
        # graphql_customer_id = customer['id']
        # customer_id = graphql_id_to_integer(graphql_customer_id)
        # request.data['customer_id'] = customer_id
        #
        # request.data._mutable = _mutable
        # return Response(request.data)
        write_serializer = self.get_serializer(data=request.data)
        if write_serializer.is_valid(raise_exception=True):
            instance = write_serializer.save()
            print(instance)
            read_serializer = ShopifyCustomerFingerprintListSerializer(instance)

            return Response(read_serializer.data)

        return Response(write_serializer.errors)
        # return super(ShopifyCustomerAddNewFingerPrint, self).create(request, *args, **kwargs)


class ShopifyCustomersFingerPrintList(ListAPIView):
    permission_classes = [ShopifyCustomerPermission, ]
    serializer_class = ShopifyCustomerFingerprintListSerializer
    queryset = None

    def get_queryset(self):
        return ShopifyCustomerFingerPrint.objects.filter(
            customer_id=self.request.data.get('customer_id'))

    def get_serializer_context(self):
        context = super(ShopifyCustomersFingerPrintList, self).get_serializer_context()
        context.update({"request": self.request})
        return context

    # def get(self, request, *args, **kwargs):
    #     return super(ShopifyCustomersFingerPrintList, self).get(request, *args, **kwargs)


class ShopifyCustomersFingerPrintListWeb(ListAPIView):
    permission_classes = [ShopifyCustomerWebPermissions, ]
    serializer_class = ShopifyCustomerFingerprintListSerializer

    # queryset = None

    def get_queryset(self):
        return ShopifyCustomerFingerPrint.objects.filter(
            customer_id=self.kwargs.get('customer_id'))

    def get_serializer_context(self):
        context = super(ShopifyCustomersFingerPrintListWeb, self).get_serializer_context()
        context.update({"request": self.request})
        return context


class ShopifyCustomerFingeprintDetail(RetrieveDestroyAPIView):
    permission_classes = [ShopifyCustomerPermission, ]
    serializer_class = ShopifyCustomerFingerPrintDetaiilSerializer
    queryset = None

    def get_object(self):
        customer_id = self.request.data.get('customer_id')
        try:
            return ShopifyCustomerFingerPrint.objects.get(pk=self.kwargs['pk'], customer_id=customer_id)
        # if fp_object and fp_object.customer_id == customer_id:
        except ShopifyCustomerFingerPrint.DoesNotExist:
            return Http404

    def destroy(self, request, *args, **kwargs):
        customer_id = self.request.data.get('customer_id')
        obj = get_object_or_404(ShopifyCustomerFingerPrint, pk=kwargs['pk'],
                                customer_id=customer_id)
        if obj:
            obj.delete()
            data = {
                'message': 'Fingerprint removed successfully.',
                'success': True
            }
            res_status = status.HTTP_200_OK
        else:
            data = {
                'message': 'Item failed to remove from wishlist.',
                'success': False
            }
            res_status = status.HTTP_404_NOT_FOUND

        return Response(data, status=res_status)


class ShopifyCustomersFingerPrintDestroy(DestroyAPIView):
    permission_classes = [ShopifyCustomerPermission, ]
    serializer_class = ShopifyCustomerFingerprintListSerializer

    def destroy(self, request, *args, **kwargs):
        customer_id = self.request.data.get('customer_id')
        obj = get_object_or_404(ShopifyCustomerFingerPrint, pk=kwargs['pk'],
                                customer_id=customer_id)
        if obj:
            obj.delete()
            data = {
                'message': 'Fingerprint removed successfully.',
                'success': True
            }
            res_status = status.HTTP_200_OK
        else:
            data = {
                'message': 'Item failed to remove from wishlist.',
                'success': False
            }
            res_status = status.HTTP_404_NOT_FOUND

        return Response(data, status=res_status)


class FingerprintRequestCreateAPIView(CreateAPIView):
    serializer_class = FingerprintRequestCreateSerializer

    # def perform_create(self, serializer):
    #     graphql_customer_id = self.request.data.get('graphql_customer_id')
    #     path_list = urlparse(base64.b64decode(graphql_customer_id).decode('utf-8')).path
    #     customer_id = os.path.split(path_list)[-1]
    #     # print(path_list)
    #     serializer.save(customer_id=customer_id)


class FingerprintRequestListAPIView(ListAPIView):
    serializer_class = FingerprintRequestSerializer
    queryset = FingerprintRequest.objects.all().order_by('-created')

    def get_queryset(self):
        graphql_customer_id = self.kwargs['graphql_customer_id']
        # path_list = urlparse(base64.b64decode(customer_id).decode('utf-8')).path
        # customer_id = os.path.split(path_list)[-1]
        return FingerprintRequest.objects.filter(graphql_customer_id=graphql_customer_id).order_by('-created')


class CustomerWishlistCreateAPIView(CreateAPIView):
    serializer_class = CustomerWishlistCreateSerializer


class CustomerWishlistListAPIView(ListAPIView):
    serializer_class = CustomerWishlistListSerializer

    def get_queryset(self):
        graphql_customer_id = self.kwargs['graphql_customer_id']
        queryset = ShopifyCustomerWishList.objects.values('product_id', 'customer_id', 'graphql_product_id',
                                                          'graphql_customer_id') \
            .filter(graphql_customer_id=graphql_customer_id).order_by('-created')

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        queryset = self.get_queryset()
        product_ids = [p['product_id'] for p in queryset]
        # graphql_product_ids = [
        #     str('gid://shopify/Product/%s' % p['product_id']) for p in queryset
        # ]
        graphql_product_ids = [p['graphql_product_id'] for p in queryset]

        response.data['product_ids'] = product_ids
        response.data['graphql_product_ids'] = graphql_product_ids
        # response.data['products'] = products
        return response


class CustomerWishlistDetailView(RetrieveAPIView, DestroyAPIView):
    serializer_class = CustomerWishlistListSerializer

    def get_queryset(self):
        graphql_customer_id = self.kwargs['graphql_customer_id']

        # customer_id = graphql_id_to_integer(graphql_customer_id)
        return ShopifyCustomerWishList.objects.filter(graphql_customer_id=graphql_customer_id)

    def get_object(self):
        graphql_customer_id = self.kwargs['graphql_customer_id']
        graphql_product_id = self.kwargs['graphql_product_id']
        obj = ShopifyCustomerWishList.objects.filter(
            graphql_customer_id=graphql_customer_id, graphql_product_id=graphql_product_id).first()
        # obj = get_object_or_404(ShopifyCustomerWishList, graphql_product_id=self.kwargs['graphql_product_id'],
        #                         graphql_customer_id=graphql_customer_id)
        return obj

    def destroy(self, request, *args, **kwargs):
        graphql_customer_id = self.kwargs['graphql_customer_id']
        graphql_product_id = self.kwargs['graphql_product_id']
        # print('delete request')
        # print(graphql_customer_id)
        obj = ShopifyCustomerWishList.objects.filter(
            graphql_customer_id=graphql_customer_id, graphql_product_id=graphql_product_id)
        if obj.exists():
            obj.delete()
            data = {
                'message': 'Item removed from wishlist successfully.',
                'success': True
            }
            res_status = status.HTTP_200_OK
        else:
            data = {
                'message': 'Item failed to remove from wishlist.',
                'success': False
            }
            res_status = status.HTTP_404_NOT_FOUND

        return Response(data, status=res_status)


class CustomerWishlistDetailViewWeb(RetrieveAPIView, DestroyAPIView):
    serializer_class = CustomerWishlistListSerializer

    def get_queryset(self):
        customer_id = self.kwargs['customer_id']

        # customer_id = graphql_id_to_integer(graphql_customer_id)
        return ShopifyCustomerWishList.objects.filter(customer_id=customer_id)

    def get_object(self):
        customer_id = self.kwargs['customer_id']
        product_id = self.kwargs['product_id']
        obj = ShopifyCustomerWishList.objects.filter(
            customer_id=customer_id, product_id=product_id).first()
        # obj = get_object_or_404(ShopifyCustomerWishList, graphql_product_id=self.kwargs['graphql_product_id'],
        #                         graphql_customer_id=graphql_customer_id)
        return obj

    def destroy(self, request, *args, **kwargs):
        graphql_customer_id = self.kwargs['graphql_customer_id']
        graphql_product_id = self.kwargs['graphql_product_id']
        # print('delete request')
        # print(graphql_customer_id)
        obj = ShopifyCustomerWishList.objects.filter(
            graphql_customer_id=graphql_customer_id, graphql_product_id=graphql_product_id)
        if obj.exists():
            obj.delete()
            data = {
                'message': 'Item removed from wishlist successfully.',
                'success': True
            }
            res_status = status.HTTP_200_OK
        else:
            data = {
                'message': 'Item failed to remove from wishlist.',
                'success': False
            }
            res_status = status.HTTP_404_NOT_FOUND

        return Response(data, status=res_status)


class AppSidebarNavigationListAPIView(APIView):
    serializer_class = AppSidebarNavigationSerializer
    queryset = AppSidebarNavigation.objects.filter(show_in_menu=True).order_by('position')

    @staticmethod
    def get(request):
        queryset = AppSidebarNavigation.objects.filter(show_in_menu=True).order_by('position')
        if queryset.exists():
            serializer = AppSidebarNavigationSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({'message': 'Nothing Found'}, status=status.HTTP_404_NOT_FOUND)


# web shopify views
class WebShopifyCustomerWishlistCreateAPIView(CreateAPIView):
    serializer_class = WebCustomerWishlistCreateSerializer

    def perform_create(self, serializer):
        customer_id = self.request.data.get('customer_id')
        product_id = self.request.data.get('product_id')
        graphql_customer_id = integer_to_graphpql_customer(customer_id)
        graphql_product_id = integer_to_graphpql_customer(product_id)
        serializer.save(graphql_customer_id=graphql_customer_id, graphql_product_id=graphql_product_id)

    def create(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        product_id = request.data.get('product_id')
        queryset = ShopifyCustomerWishList.objects.filter(customer_id=customer_id, product_id=product_id)
        if queryset.exists():
            queryset.delete()
            return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)

        return super(WebShopifyCustomerWishlistCreateAPIView, self).create(request, *args, **kwargs)


@api_view(['post'])
@permission_classes([ShopifyCustomerWebPermissions, ])
def web_wishlist_check(request):
    customer_id = request.data.get('customer_id')
    product_id = request.data.get('product_id')
    queryset = ShopifyCustomerWishList.objects.filter(customer_id=customer_id, product_id=product_id)
    if queryset.exists():
        data = {
            'success': True
        }
        return Response(data, status=status.HTTP_200_OK)

    return Response({'success': False}, status=status.HTTP_404_NOT_FOUND)


class AppCategoryListAPIView(APIView):

    @staticmethod
    def get(request):
        print('ok')
        queryset = AppCategory.objects.filter(show_in_menu=True)
        serializer = AppCategorySerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AppHomepageSliderList(APIView):
    @staticmethod
    def get(request):
        queryset = AppHomepageSlider.objects.filter(show_in_app=True)
        serializer = AppHomepageSilderSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AppHomepageBannerList(APIView):
    @staticmethod
    def get(request):
        queryset = AppHomepageBanner.objects.filter(show_in_app=True)
        serializer = AppHomepageBannerSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


# shopify collection metafields
# class ShopifyCollectionMetafields(APIView):
#
#     @staticmethod
#     def get(request):
#         admin_shopify


class AppSidebarFilterList(ListAPIView):
    serializer_class = AppSidebarFilterSerializer
    queryset = AppSidebarFilter.objects.all()

    def get_queryset(self):
        return AppSidebarFilter.objects.all().prefetch_related('tags')


class Product3DModelAPIView(CreateAPIView, RetrieveUpdateAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = Product3DModelSerializer
    queryset = Product3DModel.objects.all()

    def perform_create(self, serializer):
        serializer.save(product_id=self.kwargs['product_id'])

    def get_object(self):
        return get_object_or_404(self.get_queryset(), product_id=self.kwargs['product_id'])
        # try:
        #     return Product3DModel.objects.get(product_id=self.kwargs['product_id'])
        # except Product3DModel.DoesNotExist:
        #     return Http404

    @csrf_exempt
    def create(self, request, *args, **kwargs):
        return super(Product3DModelAPIView, self).create(request, *args, **kwargs)

    @csrf_exempt
    def update(self, request, *args, **kwargs):
        return super(Product3DModelAPIView, self).update(request, *args, **kwargs)

    @csrf_exempt
    def partial_update(self, request, *args, **kwargs):
        return super(Product3DModelAPIView, self).partial_update(request, *args, **kwargs)
