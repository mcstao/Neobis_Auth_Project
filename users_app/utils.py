from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

def send_confirmation_email(self, user):
    expiration_time = timezone.now() + timezone.timedelta(minutes=5)
    token = RefreshToken.for_user(user)
    token['exp'] = int(expiration_time.timestamp())

    protocol = self.request.scheme
    current_site = get_current_site(self.request)
    confirmation_url = f'{protocol}://{current_site.domain}/users/confirm-email/{token}/'
    subject = 'Подтвердите свою электронную почту'
    message = f'Пожалуйста, перейдите по следующей ссылке для подтверждения своей электронной почты в течение 5 минут: {confirmation_url}'
    send_mail(subject, message, settings.EMAIL_FROM, [user.email])