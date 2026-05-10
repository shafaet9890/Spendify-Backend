from rest_framework import serializers
from .models import CustomUser as User, Category, Expense
import re


# ----------Signup Serializer ------------
class SignupSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'password', 'confirm_password', 'phone']
        extra_kwargs = {
            'id'      : {'read_only': True},
            'username': {'required': True},
            'email'   : {'required': True},
            'phone'   : {'required': False},
        }

    # ---------- Field-level validations---------
    def validate_username(self, value):
        value = value.strip() # Remove leading/trailing whitespace
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_phone(self, value):
        cleaned = re.sub(r'\D', '', value)
        if len(cleaned) < 11:
            raise serializers.ValidationError("Enter a valid phone number (at least 11 digits).")
        return cleaned

    def validate_password(self, value):
        errors = []
        if not re.search(r'[A-Z]', value):
            errors.append("at least one uppercase letter")
        if not re.search(r'[0-9]', value):
            errors.append("at least one number")
        if not re.search(r'[^a-zA-Z0-9]', value):
            errors.append("at least one special character")
        if errors:
            raise serializers.ValidationError(f"Password must contain {', '.join(errors)}.")
        return value

    # -------------- Object-level validation ------------------
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data

    # -------------- Create Profile -------------
    def create(self, validated_data):
        validated_data.pop('confirm_password') # Remove confirm_password because it does not need to store in db

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
        )
        return user



# ------------- Profile Serializer (Read, Update, Delete) -----------------
class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'first_name','last_name', 'phone']
        extra_kwargs = {
            'id'      : {'read_only': True},
            'username': {'required': False},
            'email'   : {'required': False},
            'phone'   : {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    # -------------- Field-level validations ------------------

    def validate_username(self, value):
        value = value.strip()
        qs = User.objects.filter(username__iexact=value).exclude(pk=self.instance.pk) # Exclude the current user from the check
        if qs.exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        value = value.lower().strip()
        qs = User.objects.filter(email=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_phone(self, value):
        cleaned = re.sub(r'\D', '', value)
        if len(cleaned) < 11:
            raise serializers.ValidationError("Enter a valid phone number (at least 11 digits).")
        return cleaned



#------------- Change Password Serializer -------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate_password(self, value):
        errors = []
        if not re.search(r'[A-Z]', value):
            errors.append("at least one uppercase letter")
        if not re.search(r'[0-9]', value):
            errors.append("at least one number")
        if not re.search(r'[^a-zA-Z0-9]', value):
            errors.append("at least one special character")
        if errors:
            raise serializers.ValidationError(f"Password must contain {', '.join(errors)}.")
        return value

    def validate(self, data):
        user = self.context['request'].user

        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({
                "old_password": "Old password is incorrect."
            })

        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({
                "new_password2": "Passwords do not match."
            })

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password1'])
        user.save()
        return user


# ----------- Category Serializer -------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
        extra_kwargs = {
            'id'  : {'read_only': True}
        }


class ExpenseSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True) # in source "user" is the variable name in the Expense model and "username" is the field name in the User model,
    category_name = serializers.CharField(source='category.name', read_only=True)
    class Meta:
        model = Expense
        fields = ['id', 'title','user','username', 'category', 'category_name', 'amount', 'date', 'description']
        extra_kwargs = {
            'id'      : {'read_only': True},
            'user'    : {'read_only': True},
        }