from django.core.serializers import serialize
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import CustomUser, Category, Expense
from .serializer import SignupSerializer, ProfileSerializer, ExpenseSerializer, CategorySerializer, ChangePasswordSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from datetime import datetime
from django.db.models import Sum
from django.utils.timezone import now


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string



# ---------- Generate Tokens ----------------

def get_tokens_for_user(user):
    """Generate JWT access & refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access' : str(refresh.access_token),
    }


# ------------- Signup ----------------------

class SignupAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors' : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Account created successfully.',
            'data'   : serializer.data,
            'tokens' : tokens,
        }, status=status.HTTP_201_CREATED)


# ----------------- Login --------------------

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')

        password = request.data.get('password')

        # ------ Validate input --------------
        if not username or not password:
            return Response({
                'error'  : 'Username and password are required.',
            }, status=status.HTTP_400_BAD_REQUEST)

        # --------- Authentication -------------------
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({
                'error'  : 'Invalid username or password.',
            }, status=status.HTTP_401_UNAUTHORIZED)

        # ----------- For Return tokens -------------------
        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Login successful.',
            'tokens' : tokens,
            'data'   : SignupSerializer(user).data,
        }, status=status.HTTP_200_OK)


# ------------------- Logout -----------------
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'error'  : 'Refresh token is required.',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token) # Create a token instance from the provided refresh token string
            token.blacklist()
        except TokenError:
            return Response({
                'error'  : 'Token is invalid or already expired.',
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Logged out successfully.',
        }, status=status.HTTP_200_OK)


# ------------ Profile / Update / Delete ----------------------

class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # ---------- GET – fetch profile ----------------- 
    def get(self, request):
        serializer = ProfileSerializer(request.user)
        user_data = serializer.data
        return Response({
            'data'   : user_data,
        }, status=status.HTTP_200_OK)

    # ------------- PUT – update profile -----------------
    def put(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response({
                'errors' : serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response({
            'message': 'Profile updated successfully.',
            'data'   : serializer.data,
        }, status=status.HTTP_200_OK)

    # -------------- DELETE – delete account ---------------

    def delete(self, request):
        request.user.delete()
        return Response({
            'message': 'Account deleted successfully.',
        }, status=status.HTTP_204_NO_CONTENT)

class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Password updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




## ---------------User submits email ---------------------
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required.'}, status=400)

        user = CustomUser.objects.filter(email=email).first()

        if user:
            token = default_token_generator.make_token(user)
            uid   = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            send_mail(
                'Password Reset Request',
                f"""
                Hello {user.username},
                
                We received a request to reset your Spendify password.
                
                Click the link below to set a new password:
                {reset_link}
                
                This link will expire in 24 hours.
                
                If you did not request this, please ignore this email.
                
                — Spendify Team
                                """,
                'ajob720@gmail.com',
                [email],
                fail_silently=False,
            )

        # always return success — don't reveal if email exists (security)
        return Response(
            {'message': 'If this email exists a reset link has been sent.'},
            status=200
        )


## -----------------User submits new password --------------------
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid       = request.data.get('uid')
        token     = request.data.get('token')
        password1 = request.data.get('password1')
        password2 = request.data.get('password2')

        # validate all fields present
        if not all([uid, token, password1, password2]):
            return Response({'error': 'All fields are required.'}, status=400)

        # same validation as your original
        if password1 != password2:
            return Response({'error': 'Passwords do not match.'}, status=400)

        if len(password1) < 8:
            return Response({'error': 'Password must be at least 8 characters.'}, status=400)

        # decode uid — same logic as your original
        try:
            decoded_uid = urlsafe_base64_decode(uid).decode()
            user = CustomUser.objects.get(pk=decoded_uid)
        except (CustomUser.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({'error': 'Invalid reset link.'}, status=400)

        # check token — same logic as your original
        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired reset link.'}, status=400)

        # set new password — same as your original
        user.set_password(password1)
        user.save()

        return Response({'message': 'Password reset successful. You can log in now.'}, status=200)





#-------------- Category Views -----------------
class CategoryAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        categories = Category.objects.all().order_by('id')
        serializer = CategorySerializer(categories, many=True)
        return Response({
            'data'   : serializer.data,
        }, status=status.HTTP_200_OK)

# -------------- Expense Views -----------------
class ExpenseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, pk, user):
        try:
            return Expense.objects.get(pk=pk, user=user)
        except Expense.DoesNotExist:
            return None

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "errors" : serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save(user=request.user)

        return Response({
            'message': 'Expense created successfully.'}, status=status.HTTP_201_CREATED)

    def get(self, request, pk=None):
        if pk:
            try:
                expense = Expense.objects.get(id=pk, user=request.user)
            except Expense.DoesNotExist:
                return Response({"detail": "Not found"}, status=404)

            serializer = ExpenseSerializer(expense)
            return Response({
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        expenses = Expense.objects.filter(user=request.user).select_related('user', 'category')

        serializer = ExpenseSerializer(expenses, many=True)

        total_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0

        this_month_expenses = expenses.filter(
            date__year=now().year,
            date__month=now().month
        )

        total_amount_this_month = this_month_expenses.aggregate(total=Sum('amount'))['total'] or 0

        total_entries = expenses.count()

        return Response({
            'data': serializer.data,
            'total_amount': total_amount,
            'total_amount_this_month': total_amount_this_month,
            'total_entries': total_entries,
        }, status=status.HTTP_200_OK)

    # ---------- DELETE ----------------
    def delete(self, request, pk):
        expense = self.get_object(pk, request.user)
        if not expense:
            return Response({
                'error': 'Expense not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        expense.delete()
        return Response({
            'message': 'Expense deleted successfully.'
        }, status=status.HTTP_200_OK)

    # ---------- PUT (edit) ------------
    def put(self, request, pk):
        expense = self.get_object(pk, request.user)
        if not expense:
            return Response({
                'error': 'Expense not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = ExpenseSerializer(expense, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({
            'message': 'Expense updated successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)