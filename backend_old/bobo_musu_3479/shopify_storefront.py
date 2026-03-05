import requests
from django.conf import settings

storefront_api_url = url = "https://%s.myshopify.com/api/%s/graphql.json" % (
    settings.SHOPIFY_SUBDOMAIN, settings.SHOPIFY_API_VERSION
)
storefront_token = settings.SHOPIFY_STOREFRONT_ACCESS_TOKEN


def shopify_gql_request(query, variables=None):
    headers = {
        'X-Shopify-Storefront-Access-Token': storefront_token.encode('idna').decode('utf-8'),
        'Content-Type': 'application/json',
    }
    json_query = {'query': query}
    if variables:
        json_query['variables'] = variables

    print(json_query)
    response = requests.request("POST", storefront_api_url, headers=headers, json=json_query)
    res_json = response.json()

    return res_json

#
# payload = """
#     {
#         "query": "mutation customerCreate($input: CustomerInput!) {customerCreate(input: $input) {" \
#           " customer {
#     id
# email
# phone
# }userErrors {\\r\\n      field\\r\\n      message\\r\\n    }\\r\\n  }\\r\\n}\",\"variables\":{\"input\":{\"firstName\":\"Steve\",\"lastName\":\"Lastnameson\",\"email\":\"steve.lastnameson@example.com\",\"phone\":\"+15142546011\"}}}"""
