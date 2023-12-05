from django.contrib.auth import authenticate

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
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError('Пароли не совпадают')
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