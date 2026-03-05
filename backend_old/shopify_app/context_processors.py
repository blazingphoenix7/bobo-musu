import shopify


def current_shop(request):
    # if not shopify.ShopifyResource.site:
    #     return {'current_shop': None}
    # return {'current_shop': shopify.Shop.current()}
    try:
        return {'current_shop': shopify.Shop.current()}
    except:
        return {'current_shop': None}
