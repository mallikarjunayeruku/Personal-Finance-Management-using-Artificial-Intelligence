from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Personal Finance With Artificial Intelligence",
        default_version='v1',
        description="Personal Finance With Artificial Intelligence API/'s documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@myapi.local"),
        license=openapi.License(name="Apache 2.0 License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny]
)