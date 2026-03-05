from django.urls import path
from . import views

urlpatterns = [
    path("designs/", views.DesignListView.as_view(), name="design-list"),
    path("designs/<str:design_id>/", views.DesignDetailView.as_view(), name="design-detail"),
    path("designs/<str:design_id>/mesh/", views.DesignMeshView.as_view(), name="design-mesh"),
    path("preview/", views.PreviewView.as_view(), name="preview"),
]
