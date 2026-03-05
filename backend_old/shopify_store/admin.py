from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from .models import *


# Register your models here.

@admin.register(AppHomepageSlider)
class AppHomepageSliderAdmin(admin.ModelAdmin):
    list_display = ['get_heading', 'filename', 'show_in_app', 'position']
    list_editable = ['show_in_app', 'position']

    def get_heading(self, instance):
        if not instance.heading:
            return 'No Heading'
        else:
            return '%s' % instance.heading

    get_heading.short_description = 'Heading'


@admin.register(AppHomepageBanner)
class AppHomepageBannerAdmin(admin.ModelAdmin):
    list_display = ['get_heading', 'filename', 'show_in_app', 'position']
    list_editable = ['show_in_app', 'position']

    def get_heading(self, instance):
        if not instance.heading:
            return 'No Heading'
        else:
            return '%s' % instance.heading

    get_heading.short_description = 'Heading'


@admin.register(ShopifyCustomerFingerPrint)
class ShopifyCustomerFingerPrint(admin.ModelAdmin):
    list_display = ['customer_id', 'fingerprint_title', 'created', ]


@admin.register(FingerprintRequest)
class FingerprintRequestAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'graphql_customer_id', 'from_email', 'to_email', 'receiver_name', 'message',
                    'created', ]
    # list_display = ['customer_id', 'from_email', 'to_email', 'receiver_name', 'message', 'created', ]


@admin.register(ShopifyCustomerWishList)
class CustomerWishListAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'graphql_customer_id', 'product_id', 'graphql_product_id', 'created']
    # list_display = ['customer_id', 'product_id', 'created']


@admin.register(AppSidebarNavigation)
class AppSidebarNavigationAdmin(admin.ModelAdmin):
    list_display = ['name', 'human_name', 'access_route', 'method', 'icon', 'position', 'show_in_menu']
    list_editable = ['position', 'show_in_menu']
    # list_display_links = ['name']


@admin.register(AppCategory)
class AppCategoryAdmin(admin.ModelAdmin):
    list_display = ['handle', 'title', 'position', 'show_in_menu']


@admin.register(ShopifyCustomerFCMDevice)
class ShopifyCustomerFCMDeviceAdmin(admin.ModelAdmin):
    list_display = ("__str__", "device_id", "graphql_customer_id", "name", "type", "user", "active",
                    "date_created")
    list_filter = ("active",)
    actions = ("send_message", "send_bulk_message", "send_data_message",
               "send_bulk_data_message", "enable", "disable")
    raw_id_fields = ("user",)
    list_select_related = ("user",)

    # def get_search_fields(self, request):
    #     if hasattr(User, "USERNAME_FIELD"):
    #         return ("name", "device_id", "user__%s" % (User.USERNAME_FIELD))
    #     else:
    #         return ("name", "device_id")

    def send_messages(self, request, queryset, bulk=False, data=False):
        """
        Provides error handling for DeviceAdmin send_message and
        send_bulk_message methods.
        """
        ret = []
        errors = []
        total_failure = 0

        for device in queryset:
            if bulk:
                if data:
                    response = queryset.send_message(
                        data={"Nick": "Mario"}
                    )
                else:
                    response = queryset.send_message(
                        title="Test notification",
                        body="Test bulk notification"
                    )
            else:
                if data:
                    response = device.send_message(data={"Nick": "Mario"})
                else:
                    response = device.send_message(
                        title="Test notification",
                        body="Test single notification"
                    )
            if response:
                ret.append(response)

            failure = int(response['failure'])
            total_failure += failure
            errors.append(str(response))

            if bulk:
                break

        if ret:
            if errors:
                msg = _("Some messages were sent: %s" % (ret))
            else:
                msg = _("All messages were sent: %s" % (ret))
            self.message_user(request, msg)

        if total_failure > 0:
            self.message_user(
                request,
                _("Some messages failed to send. %d devices were marked as "
                  "inactive." % total_failure),
                level=messages.WARNING
            )

    def send_message(self, request, queryset):
        self.send_messages(request, queryset)

    send_message.short_description = _("Send test notification")

    def send_bulk_message(self, request, queryset):
        self.send_messages(request, queryset, True)

    send_bulk_message.short_description = _("Send test notification in bulk")

    def send_data_message(self, request, queryset):
        self.send_messages(request, queryset, False, True)

    send_data_message.short_description = _("Send test data message")

    def send_bulk_data_message(self, request, queryset):
        self.send_messages(request, queryset, True, True)

    send_bulk_data_message.short_description = _(
        "Send test data message in bulk")

    def enable(self, request, queryset):
        queryset.update(active=True)

    enable.short_description = _("Enable selected devices")

    def disable(self, request, queryset):
        queryset.update(active=False)

    disable.short_description = _("Disable selected devices")


@admin.register(AppSidebarFilter)
class AppSidebarFilterAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'tag_list']
    list_editable = ['position']
    tag_fields = ['tags']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all().order_by('name'))


@admin.register(CustomerCheckoutID)
class CustomerCheckoutIDAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'graphql_customer_id', 'checkout_id', 'created', 'updated']


@admin.register(Product3DModel)
class Product3DModelAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'created', 'updated']
