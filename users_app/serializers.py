from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from rest_framework import serializers


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=15)
    password_confirm = serializers.CharField(write_only=True, min_length=8, max_length=15)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password_confirm'
        ]

    def validate(self, data):
        errors = {}
        validate_password(data['password'])
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError('Пароли не совпадают')
        if not any(char.isdigit() for char in data['password']):
            errors['password'] = errors.get('password', []) + ['Пароль должен содержать хотя бы одну цифру.']
        if not any(char.isupper() for char in data['password']):
            errors['password'] = errors.get('password', []) + ['Пароль должен содержать хотя бы одну заглавную букву.']
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in data['password']):
            errors['password'] = errors.get('password', []) + ['Пароль должен содержать хотя бы один спецсимвол (!@#$%^&*(),.?":{}|<>).']

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        return CustomUser.objects.create_user(**validated_data)


class LoginUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.pop('username', None)
        password = data.pop('password', None)

        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError("Учетная запись не активирована.")
            else:
                raise serializers.ValidationError("Пользователь с таким логином и паролем не найден.")
        else:
            raise serializers.ValidationError("Необходимо указать логин и пароль.")

        return data


class ResendConfirmationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_message = {
        'bad_token': ('Token is expired or invalid')
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs
