import shopify
from django.conf import settings

shopify.ShopifyResource.set_site(settings.SHOPIFY_ADMIN_API_URL)
