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

from .serializers import RegisterUserSerializer, LoginUserSerializer, ResendConfirmationEmailSerializer


class RegisterUserView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            self.send_confirmation_email(user)
            return Response({'message': 'Завершите регистрацию, подтвердив по почте в течение 5 минут.'},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    send_confirmation_email = send_confirmation_email


class ConfirmEmailView(views.APIView):
    def get(self, request, token):
        try:
            decoded_token = RefreshToken(token)
            user_id = decoded_token['user_id']
            user = CustomUser.objects.get(id=user_id)
            if decoded_token['exp'] < timezone.now():
                return Response({'message': 'Срок действия ссылки подтверждения истек.'},
                                status=status.HTTP_400_BAD_REQUEST)
            user.is_active = True
            user.save()
            return Response({'message': 'Подтверждение электронной почты прошло успешно.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'message': 'Ошибка при обработке токена.'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'message': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)


class ResendConfirmationEmailView(views.APIView):
    permission_classes = [AllowAny]

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


class LoginUserView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({'user_id': user.id, 'access_token': access_token},
                            status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.clear()
                return Response({"detail": "Вы успешно вышли."}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'message': 'Ошибка при обработке токена.'}, status=status.HTTP_400_BAD_REQUEST)
