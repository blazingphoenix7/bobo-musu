import json
import os
import base64
import requests
from urllib.parse import urlparse
import urllib.request
import encodings.idna

from cryptography.fernet import Fernet
from django.conf import settings

encrypt_key = settings.FERNET_ENCRYPT_KEY.encode()


def graphql_id_to_integer(grapql_id):
    path_list = urlparse(base64.b64decode(grapql_id).decode('utf-8')).path
    main_id = os.path.split(path_list)[-1]
    return main_id


def integer_to_graphpql_customer(customer_id):
    gid = 'gid://shopify/Customer/%s' % customer_id
    return base64.b64encode(gid.encode()).decode()
    # return gid.encode()


def encrypt_file(filename):
    f = Fernet(encrypt_key)
    encrypted_data = f.encrypt(filename)

    return encrypted_data


def decrypt_file(filename):
    f = Fernet(encrypt_key)
    encrypted_data = filename.read()

    decrypted_data = f.decrypt(encrypted_data)

    return decrypted_data


def shopify_customer_token_renew(customer_access_token):
    url = "https://%s.myshopify.com/api/%s/graphql.json" % (settings.SHOPIFY_SUBDOMAIN, settings.SHOPIFY_API_VERSION)
    payload = "{\"query\":\"mutation customerAccessTokenRenew($customerAccessToken: String!) {\\r\\n  " \
              "customerAccessTokenRenew(customerAccessToken: $customerAccessToken) {\\r\\n    customerAccessToken {" \
              "\\r\\n      accessToken\\r\\n      expiresAt\\r\\n    }\\r\\n    userErrors {\\r\\n      field\\r\\n      message\\r\\n    }\\r\\n  }\\r\\n}\",\"variables\":{\"customerAccessToken\":\"%s\"}}" % customer_access_token

    headers = {
        'X-Shopify-Storefront-Access-Token': settings.SHOPIFY_STOREFRONT_ACCESS_TOKEN,
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    res_data = response.json()
    print(res_data)
    if res_data['data']['customerAccessTokenRenew']['customerAccessToken'] is not None:
        return True
    else:
        return False


#
def storefront_customer_data(access_token):
    url = "https://%s.myshopify.com/api/%s/graphql.json" % (settings.SHOPIFY_SUBDOMAIN, settings.SHOPIFY_API_VERSION)
    storefront_token = settings.SHOPIFY_STOREFRONT_ACCESS_TOKEN
    # print(storefront_token.encode().decode('ascii'))
    # encoded_storefront_token = base64.b64encode(storefront_token.encode()).decode('ascii')
    query = """
            query
                {
                  customer(customerAccessToken: "%s") {
                    id
                    lastName
                    firstName
                    email
                  }
                }
            """ % access_token

    headers = {
        'X-Shopify-Storefront-Access-Token': storefront_token.encode('idna').decode('utf-8'),
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, json={'query': query})
    res_json = response.json()
    # print(res_json)
    # print(res_json.status_code)
    # print(res_data.text)
    # print(query.encode('idna').decode('utf-8'))
    if res_json['data']['customer'] is not None:
        return res_json['data']['customer']
    else:
        return None
