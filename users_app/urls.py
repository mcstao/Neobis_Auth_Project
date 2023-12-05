from django.urls import path
from .views import RegisterUserView, LoginUserView, LogoutView, ConfirmEmailView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('confirm-email/<str:token>/', ConfirmEmailView.as_view(), name='confirm-email'),
]