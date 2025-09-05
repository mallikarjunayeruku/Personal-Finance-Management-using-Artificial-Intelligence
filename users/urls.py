from django.urls import path
from .views import RegisterView, me

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path("api/me/", me),

]
