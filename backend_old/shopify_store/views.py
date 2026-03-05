from io import BytesIO
from urllib.request import urlopen

import requests
from PIL import Image
from django.forms import model_to_dict
from django.shortcuts import render
import base64
# Create your views here.
from django.template.loader import get_template

from shopify_store.models import FingerprintRequest


def check_html_render(request):
    instance = model_to_dict(FingerprintRequest.objects.first())
    # instance = FingerprintRequest.objects.first()
    # template = get_template('email/fingerprint_request.html')
    # # msg_html = render_to_string('email/fingerprint_request.html', instance)
    # msg_html = template.render(instance)
    print(instance)
    return render(request, 'email/fingerprint_request.html', instance)


def test_base64(request):
    # image = request.data['image']
    res = requests.get('https://picsum.photos/500/500')
    image = urlopen('https://picsum.photos/500/500')
    base64_image = base64.b64encode(image.read())

    data = {
        'image': base64_image.decode("utf-8")
    }

    return render(request, 'store/fp_base64_test.html', data)
