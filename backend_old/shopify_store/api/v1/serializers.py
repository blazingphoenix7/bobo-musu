import io
import os
from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from taggit.models import Tag as TaggitTag
from taggit_serializer.serializers import TagListSerializerField, TaggitSerializer

from shopify_store.functions import graphql_id_to_integer, encrypt_file, decrypt_file
from shopify_store.models import *
from bobo_musu_3479.shopify import *
from bobo_musu_3479.shopify_storefront import shopify_gql_request
import base64
import uuid
from urllib.parse import urlparse


class ShopifyWebCustomerRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=32, required=False, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(max_length=32, required=True)
    email = serializers.EmailField(max_length=32, required=True)

    phone = serializers.CharField(max_length=32, required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(max_length=32, required=True)
    password_confirmation = serializers.CharField(max_length=32, required=True)

    def validate(self, data):
        """
        Check that the blog post is about Django.
        """
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError({'password_confirmation': 'Password not matched'})
        return data

    @staticmethod
    def validate_password(value):
        if len(value) < 8:
            raise serializers.ValidationError('Minimum 8 charecters required')
        return value

    @staticmethod
    def validate_phone(value):

        if value != "" and len(value) < 8:
            raise serializers.ValidationError('Minimum 8 charecters required')
        return value

    def create(self, validated_data):
        print(validated_data)
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        phone = validated_data.pop('phone')
        gql_query = """
            mutation customerCreate($input: CustomerCreateInput!) {
              customerCreate(input: $input) {
                customer {
                  id
                }
                customerUserErrors {
                  code
                  field
                  message
                }
              }
            }
        """

        variables = {
            "input": {
                "lastName": last_name.title(),
                "email": validated_data.pop('email'),
                "password": validated_data.pop('password_confirmation')
            }
        }

        if first_name != "":
            variables['input']['firstName'] = first_name.title()

        if phone != "":
            variables['input']['phone'] = phone

        res_json = shopify_gql_request(gql_query, variables)
        return res_json


# ShopifyCustomerFingerPrint Default Serializer
class ShopifyCustomerFingerPrintSerializer(serializers.ModelSerializer):
    # customer_id = serializers.CharField(required=False)
    # fingerprint_file = serializers.FileField(required=True)

    class Meta:
        model = ShopifyCustomerFingerPrint
        fields = '__all__'
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShopifyCustomerFingerPrint.objects.all(),
                fields=('customer_id', 'fingerprint_title'),
                message=_("Title Exist for this customer.")
            )
        ]

    # encrypt files when create
    # def create(self, validated_data):
    #     # graphql_customer_id = validated_data.get('graphql_customer_id')
    #     # customer_id = graphql_id_to_integer(graphql_customer_id)
    #     # validated_data['customer_id'] = customer_id
    #     # print(validated_data)
    #
    #     image = validated_data.pop('fingerprint_file')
    #     # obj_filename = '%s.bm' % image.name
    #     obj_filename = '%s.bm' % uuid.uuid4()
    #     image_data = image.encode()
    #     encrypted_data = encrypt_file(image_data)
    #     file_content = ContentFile(encrypted_data)
    #     instance = super(ShopifyCustomerFingerPrintSerializer, self).create(validated_data)
    #     instance.fingerprint_file.save(obj_filename, file_content)
    #     # return super().create(validated_data)
    #     return instance

    # def get_unique_together_validators(self):

    # def validate(self, attrs):
    #     customer_id = attrs.get('customer_id')
    #     fingerprint_title = attrs.get('fingerprint_title')
    #     obj = ShopifyCustomerFingerPrint.objects.filter(customer_id=customer_id, fingerprint_title=fingerprint_title)
    #     if obj.exists():
    #         raise serializers.ValidationError('customer_id with fingerprint_title already exists')
    #     else:
    #         return attrs


class ShopifyCustomerFingerprintListSerializer(serializers.ModelSerializer):
    # fingerprint_file = serializers.SerializerMethodField(method_name='file_url')

    class Meta:
        model = ShopifyCustomerFingerPrint
        fields = ['id', 'fingerprint_title', 'fingerprint_file', 'customer_id', 'graphql_customer_id', 'created',
                  'updated']

    def file_url(self, instance):
        new_url = '{}?id={}'.format(instance.fingerprint_file.url, instance.id)
        return self.context['request'].build_absolute_uri(new_url)


class ShopifyCustomerFingerPrintDetaiilSerializer(serializers.ModelSerializer):
    # file_data = serializers.SerializerMethodField(method_name='get_fingerprint_data', read_only=True)

    class Meta:
        model = ShopifyCustomerFingerPrint
        fields = ['id', 'fingerprint_title', 'fingerprint_file', 'customer_id', 'graphql_customer_id', 'created',
                  'updated', ]

    @staticmethod
    def get_fingerprint_data(instance):
        decrypted_file = decrypt_file(instance.fingerprint_file)

        return decrypted_file


class FingerprintRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FingerprintRequest
        fields = '__all__'


class FingerprintRequestCreateSerializer(serializers.ModelSerializer):
    # graphql_customer_id = serializers.CharField(allow_blank=True, write_only=True)
    # customer_id = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = FingerprintRequest
        fields = '__all__'
        # fields = [
        #     'graphql_customer_id',
        #     'from_email',
        #     'to_email',
        #     'sender_name',
        #     'receiver_name',
        #     'message',
        # ]

    def get_serializer_context(self):
        return self.context['request'].data

    def validate(self, attrs):
        if attrs['from_email'] == attrs['to_email']:
            raise serializers.ValidationError('Sender and receiver email can not be the same')

        # if 'graphql_customer_id' not in attrs or attrs['graphql_customer_id'] == "":
        #     raise serializers.ValidationError('graphql_customer_id field can not be empty')
        #
        # elif 'graphql_customer_id' in attrs:
        #     graphql_customer_id = attrs.pop('graphql_customer_id')
        #     path_list = urlparse(base64.b64decode(graphql_customer_id).decode('utf-8')).path
        #     customer_id = os.path.split(path_list)[-1]
        #     attrs['customer_id'] = customer_id

        return super().validate(attrs)

    def create(self, validated_data):
        graphql_customer_id = validated_data.get('graphql_customer_id')
        customer_id = graphql_id_to_integer(graphql_customer_id)
        validated_data['customer_id'] = customer_id
        return super().create(validated_data)


class CustomerWishlistCreateSerializer(serializers.ModelSerializer):
    graphql_customer_id = serializers.CharField(required=True)
    graphql_product_id = serializers.CharField(required=True)

    class Meta:
        model = ShopifyCustomerWishList
        fields = '__all__'

    def validate(self, attrs):
        graphql_customer_id = attrs['graphql_customer_id']
        graphql_product_id = attrs['graphql_product_id']
        data_obj = ShopifyCustomerWishList.objects.filter(graphql_customer_id=graphql_customer_id,
                                                          graphql_product_id=graphql_product_id)

        if data_obj.exists():
            raise serializers.ValidationError('You can not add same product to wishlist for same customer.')

        return super().validate(attrs)

    def create(self, validated_data):
        graphql_customer_id = validated_data.get('graphql_customer_id')
        graphql_product_id = validated_data.get('graphql_product_id')
        customer_id = graphql_id_to_integer(graphql_customer_id)
        product_id = graphql_id_to_integer(graphql_product_id)
        validated_data['customer_id'] = customer_id
        validated_data['product_id'] = product_id
        print(validated_data)
        return super().create(validated_data)


class AppHomepageSilderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppHomepageSlider
        fields = '__all__'


class AppHomepageBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppHomepageBanner
        fields = '__all__'


class WebCustomerWishlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopifyCustomerWishList
        fields = '__all__'

    # def create(self, validated_data):
    #     graphql_customer_id = validated_data.get('customer_id')
    #     graphql_product_id = validated_data.get('product_id')
    #     customer_id = customer_id = validated_data.get('customer_id')
    #     product_id = validated_data.get('graphql_product_id')
    #     validated_data['graphql_customer_id'] = str(graphql_customer_id)
    #     validated_data['graphql_product_id'] = str(graphql_product_id)
    #     print(validated_data)
    #     return super().create(validated_data)


class CustomerWishlistListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopifyCustomerWishList
        fields = '__all__'


class AppSidebarNavigationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSidebarNavigation
        fields = '__all__'


class AppCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppCategory
        fields = '__all__'


class ShopifyCustomerFCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopifyCustomerFCMDevice
        fields = '__all__'


class TagListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaggitTag
        fields = '__all__'


class AppSidebarFilterSerializer(TaggitSerializer, serializers.ModelSerializer):
    # tags = TagListSerializerField()
    tags = serializers.SerializerMethodField(method_name='get_tags_set')

    class Meta:
        model = AppSidebarFilter
        fields = '__all__'

    def get_tags_set(self, instance):
        tags_all = instance.tags.all().values_list('name', flat=True).order_by('name')
        # print(tags_all)
        # return TagListSerializer(tags_all, many=True).data
        return tags_all


class APPCustomerCheckoutIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerCheckoutID
        fields = '__all__'


class Product3DModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product3DModel
        fields = '__all__'

        extra_kwargs = {
            'product_id': {
                'read_only': True
            }
        }
