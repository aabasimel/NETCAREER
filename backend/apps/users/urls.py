from django.urls import include, path
from rest_framework.routers import DefaultRouter
from django.views.generic import RedirectView


from . import views


router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", views.UserRegistrationView.as_view(), name="register"),
    path("auth/login/", views.UserLoginView.as_view(), name="login"),
    path("auth/verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("auth/logout/", views.UserLogoutView.as_view(), name="logout"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
]
