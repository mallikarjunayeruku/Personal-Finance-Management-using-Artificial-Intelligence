
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/', include('finance.urls')),
    path('api/users/', include('users.urls')),
    path('', RedirectView.as_view(url='/login/')),
    path('login/', TemplateView.as_view(template_name='m3/login.html')),
    path('register/', TemplateView.as_view(template_name='m3/register.html')),
    path('dashboard/', TemplateView.as_view(template_name='m3/dashboard.html')),

    path("api/", include("finance.urls")),

]
