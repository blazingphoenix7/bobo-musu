from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def shopify_product_link(handle):
    shopify_domain = settings.SHOPIFY_DOMAIN
    return 'https://{}/products/{}'.format(shopify_domain, handle)
