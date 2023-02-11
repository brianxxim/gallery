from django.apps import AppConfig


class PhotosConfig(AppConfig):
    name = 'photos'

    def ready(self):
        # 初始化用户
        from .models import User
        from django.conf import settings

        public_image_user = User.objects.filter(username=settings.PUBLIC_USER_USERNAME).first()

        if public_image_user is None:
            public_image_user = User.objects.create(username=settings.PUBLIC_USER_USERNAME)
            public_image_user.is_staff = True
            public_image_user.set_password(settings.PUBLIC_USER_PASSWORD)

        if settings.DEBUG:
            public_image_user.is_superuser = True

        public_image_user.save()
