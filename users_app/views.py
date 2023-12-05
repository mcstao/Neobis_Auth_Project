from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import views
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser

from .serializers import RegisterUserSerializer, LoginUserSerializer


class RegisterUserView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            self.send_confirmation_email(user)
            return Response({'message': '.'},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_confirmation_email(self, user, request):
        expiration_time = timezone.now() + timezone.timedelta(minutes=5)
        token = RefreshToken.for_user(user)
        token['exp'] = int(expiration_time.timestamp())

        token = RefreshToken.for_user(user)
        current_site = get_current_site(request)
        confirmation_url = f'https://{current_site.domain}/confirm-email/{token}/'
        subject = 'Подтвердите свою электронную почту'
        message = f'Пожалуйста, перейдите по следующей ссылке для подтверждения своей электронной почты в течении 5 минут: {confirmation_url}'
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])


class ConfirmEmailView(views.APIView):
    def get(self, request, token):
        try:
            decoded_token = RefreshToken(token)
            user_id = decoded_token['user_id']
            user = CustomUser.objects.get(id=user_id)
            if decoded_token['exp'] < timezone.now():
                return Response({'message': 'Срок действия ссылки подтверждения истек.'}, status=status.HTTP_400_BAD_REQUEST)
            user.is_active = True
            user.save()
            return Response({'message': 'Подтверждение электронной почты прошло успешно.'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'message': 'Ошибка при обработке токена.'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'message': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)



class LoginUserView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response({'user_id': user.id, 'email': user.email}, status=status.HTTP_200_OK)
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
