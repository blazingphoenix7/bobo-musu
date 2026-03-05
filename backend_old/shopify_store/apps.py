from django.apps import AppConfig


class ShopifyStoreConfig(AppConfig):
    name = 'shopify_store'

    def ready(self):
        import shopify_store.signals
