from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import FileExtensionValidator
from django.db import transaction

from .models import Profile

User = get_user_model()


class BootstrapFields:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            field.widget.attrs["aria-describedby"] = f"id_{name}_help id_{name}_errors"


class LoginForm(BootstrapFields, AuthenticationForm):
    username = forms.CharField(label="Логин", max_length=150, widget=forms.TextInput(
        attrs={"autocomplete": "username", "autofocus": True},
    ))


class SignupForm(BootstrapFields, UserCreationForm):
    email = forms.EmailField(label="Email", max_length=254)
    first_name = forms.CharField(label="Имя", max_length=50)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name")

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.create(user=user, nickname=user.first_name)
        return user


class AvatarField(forms.ImageField):
    def to_python(self, data):
        if data and data.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Файл должен быть не больше 2 МБ.")
        image = super().to_python(data)
        if image and image.image.format not in {"JPEG", "PNG"}:
            raise forms.ValidationError("Загрузите изображение в формате JPG или PNG.")
        if image and max(image.image.size) > 4096:
            raise forms.ValidationError("Ширина и высота аватара должны быть не больше 4096 пикселей.")
        return image


class ProfileForm(BootstrapFields, forms.ModelForm):
    email = forms.EmailField(label="Email", max_length=254)
    nickname = forms.CharField(label="Отображаемое имя", max_length=50)
    avatar = AvatarField(
        label="Аватар", required=False,
        help_text="JPG или PNG, до 2 МБ. Пустое поле сохраняет текущий аватар.",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png"])],
        widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png"}),
    )

    class Meta:
        model = Profile
        fields = ("email", "nickname", "avatar")

    def __init__(self, *args, user, **kwargs):
        self.user = user
        kwargs["initial"] = {
            "email": user.email,
            "nickname": kwargs["instance"].nickname or user.get_full_name() or user.get_username(),
        }
        super().__init__(*args, **kwargs)

    @transaction.atomic
    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user = self.user
        if commit:
            profile.save()
            self.user.email = self.cleaned_data["email"]
            self.user.save(update_fields=["email"])
        return profile
