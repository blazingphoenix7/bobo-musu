from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail, EmailMessage
from django.forms import model_to_dict
from django.template.loader import render_to_string, get_template
from django.utils.html import strip_tags

from shopify_store.models import FingerprintRequest, ShopifyCustomerFCMDevice


def send_html_email(emails, subject, template_name, context, sender):
    msg_html = render_to_string(template_name, context=context)
    msg = EmailMessage(subject=subject, body=msg_html, from_email=sender, to=emails)
    msg.content_subtype = "html"  # Main content is now text/html
    return msg.send()


@receiver(post_save, sender=FingerprintRequest)
def send_fingerprint_request_email(sender, created, instance, **kwargs):

    data = model_to_dict(instance)
    if created:
        mail_subject = '{} sent you a Fingerprint Request'.format(instance.sender_name)
        try:
            emails = [instance.to_email]
            send_html_email(emails, mail_subject, 'email/fingerprint_request.html', data, instance.from_email)

        except Exception as e:
            print(e)


def check_html_render():
    instance = model_to_dict(FingerprintRequest.objects.first())
    template = get_template('email/fingerprint_request.html')
    # msg_html = render_to_string('email/fingerprint_request.html', instance)
    msg_html = template.render(instance)
    # print(instance)
    print(msg_html)


@receiver(post_save, sender=ShopifyCustomerFCMDevice)
def send_device_add_notification(sender, created, instance, **kwargs):
    if created:
        print('new device added')
        print(instance)
        instance.send_message("New Device", "You added a new device")



