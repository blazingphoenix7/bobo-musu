import os

from django.core.exceptions import ValidationError
from django.db import models
from taggit.managers import TaggableManager
from django.utils.translation import gettext_lazy as _
from fcm_django.models import AbstractFCMDevice
# Create your models here.
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill


class ShopifyCustomerFCMDevice(AbstractFCMDevice):
    graphql_customer_id = models.CharField(max_length=250, null=False, default=None)

    class Meta:
        verbose_name = _('Shopify Customer FCM device')
        verbose_name_plural = _('Shopify Customer FCM devices')


def shopify_customer_fingerprint_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'shopify/customers/customer_{0}/{1}'.format(instance.customer_id, filename)


class ShopifyCustomerFingerPrint(models.Model):
    customer_id = models.BigIntegerField(null=False, default=None, help_text='Shopify customer ID')
    graphql_customer_id = models.CharField(max_length=250, null=False, default=None)
    fingerprint_title = models.CharField(max_length=32, default=None, null=True)
    fingerprint_file = models.FileField(upload_to=shopify_customer_fingerprint_directory_path, null=False,
                                        default=None, help_text='Customer Fingerprint File')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Customer Fingerprint'
        verbose_name_plural = 'Customer Fingerprints'
        constraints = [
            models.UniqueConstraint(fields=['customer_id', 'fingerprint_title'],
                                    name='unique_customer_fingerprint_file')]


class FingerprintRequest(models.Model):
    customer_id = models.BigIntegerField(null=False, default=None, )
    graphql_customer_id = models.CharField(max_length=250, default=None, null=False)
    from_email = models.EmailField(null=False)
    to_email = models.EmailField(null=False)
    sender_name = models.CharField(max_length=32, default=None, null=True)
    receiver_name = models.CharField(max_length=32, default=None, null=True)
    message = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Fingerprint Request'
        verbose_name_plural = 'Fingerprint Requests'


class ShopifyCustomerWishList(models.Model):
    product_id = models.BigIntegerField(null=False, default=None)
    graphql_product_id = models.CharField(max_length=250, null=False, default=None)
    customer_id = models.BigIntegerField(null=False, default=None)
    graphql_customer_id = models.CharField(max_length=250, null=False, default=None)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if ShopifyCustomerWishList.objects.filter(
                customer_id=self.customer_id,
                product_id=self.product_id
        ).exists():
            raise ValidationError(_('Product in customer wishlist already exist.'))
        else:
            super(ShopifyCustomerWishList, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Product Wishlist'
        verbose_name_plural = 'Product Wishlist'


class AppSidebarNavigation(models.Model):
    name = models.CharField(max_length=32, default=None, null=False)
    human_name = models.CharField(max_length=32, default=None, null=False)
    access_route = models.CharField(max_length=32, default=None, null=True, blank=True)
    method = models.CharField(max_length=32, default=None, null=True, blank=True)
    icon = models.CharField(max_length=32, default=None, null=True)
    # slug = models.SlugField(max_length=32, default=None, null=False)

    show_in_menu = models.BooleanField(default=False)
    registered_user_only = models.BooleanField(default=False)
    position = models.IntegerField(default=None)

    def __str__(self):
        return '%s' % self.name

    class Meta:
        ordering = ('position',)
        verbose_name = 'App Sidebar Menu'
        verbose_name_plural = 'App Sidebar Menu'


class AppCategory(models.Model):
    title = models.CharField(max_length=120, default=None, null=False)
    handle = models.CharField(unique=True, max_length=120, default=None, null=False)

    show_in_menu = models.BooleanField(default=False)
    position = models.IntegerField(default=None)

    def __str__(self):
        return '%s' % self.title

    class Meta:
        ordering = ('position',)
        verbose_name = 'App Category'
        verbose_name_plural = 'App Categories'


class AppHomepageSlider(models.Model):
    heading = models.CharField(max_length=120, default=None, null=True, blank=True)
    sub_heading = models.CharField(max_length=120, default=None, null=True, blank=True)
    show_in_app = models.BooleanField(default=False)
    position = models.IntegerField(default=None)

    image = ProcessedImageField(upload_to='homepage/sliders/',
                                format='PNG',
                                processors=[ResizeToFill(1200, 600)],
                                null=False,
                                default=None)

    @property
    def filename(self):
        return os.path.basename(self.image.name)

    def __str__(self):
        str_text = self.heading
        if not self.heading:
            str_text = self.filename

        return '%s' % str_text

    def __unicode__(self):
        return '%s' % self.id

    class Meta:
        ordering = ('-position',)
        verbose_name = 'Homepage Slider'
        verbose_name_plural = 'Homepage Sliders'


class AppHomepageBanner(models.Model):
    heading = models.CharField(max_length=120, default=None, null=True, blank=True)
    sub_heading = models.CharField(max_length=120, default=None, null=True, blank=True)
    show_in_app = models.BooleanField(default=False)
    position = models.IntegerField(default=None)

    image = ProcessedImageField(upload_to='homepage/banners/',
                                format='PNG',
                                processors=[ResizeToFill(1200, 600)],
                                null=False,
                                default=None)

    @property
    def filename(self):
        return os.path.basename(self.image.name)

    def __str__(self):
        str_text = self.heading
        if not self.heading:
            str_text = self.filename

        return '%s' % str_text

    def __unicode__(self):
        return '%s' % self.id

    class Meta:
        ordering = ('-position',)
        verbose_name = 'Homepage Banner'
        verbose_name_plural = 'Homepage Banners'


class AppSidebarFilter(models.Model):
    title = models.CharField(_('Title'), max_length=120, null=False, blank=False)
    # tags = models.CharField(_('Tags'), max_length=500, default=None, null=True)
    tags = TaggableManager(_('Tags'))

    position = models.IntegerField(_('Position'), default=None, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_tags_display(self):
        return self.tags.values_list('name', flat=True)

    def __str__(self):
        return '%s' % self.title

    def __unicode__(self):
        return '%s' % self.id

    class Meta:
        ordering = ('position',)
        verbose_name = 'App Sidebar Filter'
        verbose_name_plural = 'App Sidebar Filters'


class CustomerCheckoutID(models.Model):
    customer_id = models.BigIntegerField(unique=True, null=False, default=None)
    graphql_customer_id = models.CharField(unique=True, max_length=250, null=False, default=None)
    checkout_id = models.CharField(max_length=500, null=False, default=None)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Customer Checkout ID'
        verbose_name_plural = 'Customer Checkout ID'


class Product3DModel(models.Model):
    product_id = models.BigIntegerField(unique=True, null=False, default=None)
    model_file = models.FileField(upload_to='3d_models/', null=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product 3D Model'
        verbose_name_plural = 'Product 3D Models'
