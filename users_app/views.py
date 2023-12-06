from datetime import datetime

from drf_spectacular.utils import extend_schema

from .utils import send_confirmation_email
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import views
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser

from .serializers import RegisterUserSerializer, LoginUserSerializer, ResendConfirmationEmailSerializer, \
    LogoutSerializer


@extend_schema(
    description='Этот эндпоинт служит для регистрации пользователя'
)
class RegisterUserView(views.APIView):
    serializer_class = RegisterUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            self.send_confirmation_email(user)
            return Response({'message': 'Завершите регистрацию, подтвердив по почте в течение 5 минут.'},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    send_confirmation_email = send_confirmation_email


@extend_schema(
    description='Этот эндпоинт служит для подтверждение почты',
    responses={200: {'description': 'Подтверждение электронной почты прошло успешно'}}
)
class ConfirmEmailView(views.APIView):
    def get(self, request, token):
        try:
            decoded_token = RefreshToken(token)
            user_id = decoded_token['user_id']
            user = CustomUser.objects.get(id=user_id)
            exp_timestamp = decoded_token['exp']
            exp_datetime = datetime.fromtimestamp(exp_timestamp, timezone.utc)
            if exp_datetime < timezone.now():
                return Response({'message': 'Срок действия ссылки подтверждения истек.'},
                                status=status.HTTP_400_BAD_REQUEST)
            user.is_active = True
            user.save()
            return Response({'message': 'Подтверждение электронной почты прошло успешно.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'message': 'Ошибка при обработке токена.'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'message': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    description='Этот эндпоинт служит для повторной отправки письма подтверждения почты'
)
class ResendConfirmationEmailView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = ResendConfirmationEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = ResendConfirmationEmailSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user = CustomUser.objects.get(email=serializer.validated_data['email'])
            except ObjectDoesNotExist:
                return Response({'detail': 'Не найдено учетной записи с указанными данными'},
                                status=status.HTTP_404_NOT_FOUND)

            if user.is_active:
                return Response({'detail': 'Почта уже подтверждена'}, status=status.HTTP_400_BAD_REQUEST)

            send_confirmation_email(self, user)
            return Response({'message': 'Повторное письмо с подтверждением отправлено'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    description='Этот эндпоинт служит для логина пользователя'
)
class LoginUserView(views.APIView):
    serializer_class = LoginUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = LoginUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)

            return Response({'user_id': user.id, 'access': access},
                            status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    description='Этот эндпоинт служит для выхода пользователя'
)
class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        if serializer.is_valid():
            try:
                refresh_token = request.data.get("refresh")
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"detail": "Вы успешно вышли."}, status=status.HTTP_200_OK)
            except TokenError:
                return Response({'message': 'Ошибка при обработке токена.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Некоторые данные не были валидными'}, status=status.HTTP_400_BAD_REQUEST)
