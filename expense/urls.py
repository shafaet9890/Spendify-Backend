from django.urls import path
from .views import SignupAPIView, LoginAPIView, ProfileAPIView, LogoutAPIView, CategoryAPIView,ExpenseAPIView, ChangePasswordAPIView, PasswordResetRequestView, PasswordResetConfirmView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('signup/', SignupAPIView.as_view(), name='signup'),
    path('profile/', ProfileAPIView.as_view(), name='profile'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),#default view
    path('categories/', CategoryAPIView.as_view(), name='categories'),
    path('expenses/', ExpenseAPIView.as_view(), name='expenses'),
    path('expenses/<int:pk>/', ExpenseAPIView.as_view(), name='expenses_details'),
    path('change_password/',ChangePasswordAPIView.as_view(),name='change_password'),
    # password reset
    path('forgot-password/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('reset-password/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
