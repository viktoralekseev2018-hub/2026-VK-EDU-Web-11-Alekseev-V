from django import forms
from django.db import transaction

from core.forms import BootstrapFields
from .models import Answer, Question, Tag


class AskForm(BootstrapFields, forms.ModelForm):
    title = forms.CharField(label="Заголовок", min_length=10, max_length=150,
                            help_text="От 10 до 150 символов.")
    text = forms.CharField(label="Текст вопроса", min_length=20, max_length=5000,
                           help_text="От 20 до 5 000 символов.",
                           widget=forms.Textarea(attrs={"rows": 6}))
    tag_names = forms.CharField(label="Теги", max_length=80,
                                help_text="От одного до трёх тегов через запятую.")

    class Meta:
        model = Question
        fields = ("title", "text", "tag_names")

    def clean_tag_names(self):
        tags = [tag.strip().lower() for tag in self.cleaned_data["tag_names"].split(",")]
        if not 1 <= len(tags) <= 3 or any(not tag or "/" in tag for tag in tags):
            raise forms.ValidationError("Укажите от одного до трёх непустых тегов без символа «/».")
        return sorted(set(tags))

    @transaction.atomic
    def save(self, commit=True, *, author):
        question = super().save(commit=False)
        question.author = author
        if commit:
            question.save()
            tags = [Tag.objects.get_or_create(name=name)[0] for name in self.cleaned_data["tag_names"]]
            question.tags.set(tags)
        return question


class AnswerForm(BootstrapFields, forms.ModelForm):
    text = forms.CharField(label="Текст ответа", min_length=10, max_length=5000,
                           help_text="От 10 до 5 000 символов.",
                           widget=forms.Textarea(attrs={"rows": 5}))

    class Meta:
        model = Answer
        fields = ("text",)

    def save(self, commit=True, *, question, author):
        answer = super().save(commit=False)
        answer.question = question
        answer.author = author
        if commit:
            answer.save()
        return answer


class VoteForm(forms.Form):
    value = forms.TypedChoiceField(choices=[(-1, "Дизлайк"), (1, "Лайк")], coerce=int)


class CorrectAnswerForm(forms.Form):
    question_id = forms.IntegerField(min_value=1, max_value=2**63 - 1)
    answer_id = forms.IntegerField(min_value=1, max_value=2**63 - 1)
    selected = forms.TypedChoiceField(choices=[("0", "Снять"), ("1", "Отметить")],
                                      coerce=lambda value: value == "1")
