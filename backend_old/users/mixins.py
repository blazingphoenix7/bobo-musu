from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse


class AdminLoginRequired(LoginRequiredMixin):
    def get_login_url(self):
        return '/admin/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and not (request.user.is_staff or request.user.is_superuser):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdminPermissionMixin(PermissionRequiredMixin):
    pass
