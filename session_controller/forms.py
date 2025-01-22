from django import forms
from .models import Competency, Profile
import os


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150, label="Имя пользователя")
    password = forms.CharField(
        widget=forms.PasswordInput, label="Пароль", min_length=4)


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())


class CompetencyForm(forms.ModelForm):
    class Meta:
        model = Competency
        fields = ['name', 'description', 'level']  # Пример полей модели

    # Поле для описания с textarea
    description = forms.CharField(
        widget=forms.Textarea, label="Description", required=True)

    # Пример поля с выбором уровня компетенции
    level = forms.ChoiceField(choices=[('beginner', 'Beginner'), (
        'intermediate', 'Intermediate'), ('advanced', 'Advanced')], label="Level", required=True)

    class Media:
        css = {
            'all': ('competency_form.css',)  # Стиль для формы
        }
        js = ('competency_form.js',)  # Скрипты для формы


class ProfileAvatarForm(forms.ModelForm):
    delete_avatar = forms.BooleanField(
        required=False, label="Удалить аватар", widget=forms.CheckboxInput)

    class Meta:
        model = Profile
        fields = ['avatar']
        exclude = ['user']  # Исключаем поле user
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'avatar': 'Аватар'
        }
        help_texts = {
            'avatar': 'Загрузите изображение аватара.'
        }
        error_messages = {
            'avatar': {
                'invalid': 'Неверный формат файла. Пожалуйста, загрузите изображение.'
            }
        }

    def clean(self):
        cleaned_data = super().clean()
        delete_avatar = cleaned_data.get('delete_avatar')

        # Убираем аватар, если галочка отмечена
        if delete_avatar:
            avatar_field = self.instance.avatar
            if avatar_field:  # Если аватар существует, удалим файл
                if os.path.isfile(avatar_field.path):
                    os.remove(avatar_field.path)
            cleaned_data['avatar'] = None

        return cleaned_data
