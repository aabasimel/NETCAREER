from django.urls import include, path
from rest_framework.routers import DefaultRouter
from django.views.generic import RedirectView


from . import views

from .views import (
    google_oauth_initiate,
    get_auth_token,
    check_auth_method,
    social_user_set_password,
    set_password_direct,
)

router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/register/", views.UserRegistrationView.as_view(), name="register"),
    path("auth/login/", views.UserLoginView.as_view(), name="login"),
    path("auth/verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("auth/logout/", views.UserLogoutView.as_view(), name="logout"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path(
        "google/login/",
        RedirectView.as_view(url="/accounts/google/login/"),
        name="google_login",
    ),
    path("api/auth/google/initiate/", google_oauth_initiate, name="google_oauth_docs"),
    path("api/auth/token/", get_auth_token, name="get_token"),
    path("auth/method/", check_auth_method, name="check_auth_method"),
    path(
        "auth/social/set-password/",
        social_user_set_password,
        name="social_set_password",
    ),
    path(
        "auth/social/set-password-direct/",
        set_password_direct,
        name="set_password_direct",
    ),
]
