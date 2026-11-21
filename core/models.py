from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.templatetags.static import static


def avatar_upload_path(instance, filename):
    return f"avatars/{uuid4().hex}{Path(filename).suffix.lower()}"


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    nickname = models.CharField("Отображаемое имя", max_length=50, blank=True)
    avatar = models.ImageField(
        "Аватар", upload_to=avatar_upload_path, blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png"])],
    )

    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self):
        return self.user.get_username()

    @property
    def avatar_url(self):
        return self.avatar.url if self.avatar else static("core/img/avatar-1.svg")
