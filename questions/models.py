from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone


def related_total(model, foreign_key, aggregate):
    rows = model.objects.filter(**{foreign_key: OuterRef("pk")}).order_by().values(foreign_key)
    return Coalesce(Subquery(rows.annotate(total=aggregate).values("total")), 0)


def vote_value(model, foreign_key, user):
    if not user or not user.is_authenticated:
        return Value(0)
    vote = model.objects.filter(**{foreign_key: OuterRef("pk")}, user=user).values("value")
    return Coalesce(Subquery(vote), 0)


class TagQuerySet(models.QuerySet):
    def popular(self):
        return self.annotate(count=Count("questions")).order_by("-count", "name")[:8]


class Tag(models.Model):
    name = models.CharField("Название", max_length=80, unique=True)
    objects = TagQuerySet.as_manager()

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "теги"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("questions:tag", args=[self.name])


class QuestionQuerySet(models.QuerySet):
    def cards(self, user=None):
        return self.select_related("author__profile").prefetch_related("tags").annotate(
            rating=related_total(QuestionLike, "question_id", Sum("value")),
            answers_count=related_total(Answer, "question_id", Count("pk")),
            my_vote=vote_value(QuestionLike, "question_id", user),
        )

    def newest(self, user=None):
        return self.cards(user).order_by("-created_at", "-pk")

    def popular(self, user=None):
        return self.cards(user).order_by("-rating", "-pk")

    def by_tag(self, tag, user=None):
        return self.newest(user).filter(tags=tag)

    def search(self, query):
        if not query:
            return self
        tagged = Tag.objects.filter(questions=OuterRef("pk"), name__icontains=query)
        return self.filter(Q(title__icontains=query) | Q(text__icontains=query) | models.Exists(tagged))

    def top_authors(self):
        return self.values("author__username").annotate(total=Count("pk")).order_by("-total", "author__username")[:5]


class Publication(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор")
    text = models.TextField("Текст")
    created_at = models.DateTimeField("Дата публикации", default=timezone.now, db_index=True)

    class Meta:
        abstract = True


class Question(Publication):
    title = models.CharField("Заголовок", max_length=200)
    tags = models.ManyToManyField(Tag, related_name="questions", verbose_name="Теги", blank=True)
    objects = QuestionQuerySet.as_manager()

    class Meta:
        verbose_name = "вопрос"
        verbose_name_plural = "вопросы"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("questions:question", args=[self.pk])


class AnswerQuerySet(models.QuerySet):
    def for_question(self, question, user=None):
        return self.filter(question=question).select_related("author__profile").annotate(
            rating=related_total(AnswerLike, "answer_id", Sum("value")),
            my_vote=vote_value(AnswerLike, "answer_id", user),
        ).order_by("-is_correct", "created_at", "pk")


class Answer(Publication):
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE, verbose_name="Вопрос")
    is_correct = models.BooleanField("Правильный ответ", default=False)
    objects = AnswerQuerySet.as_manager()

    class Meta:
        verbose_name = "ответ"
        verbose_name_plural = "ответы"

    def __str__(self):
        return self.text[:80]

    def url_on_page(self, per_page):
        earlier = Q(created_at__lt=self.created_at) | Q(created_at=self.created_at, pk__lt=self.pk)
        before = Q(is_correct=self.is_correct) & earlier
        if not self.is_correct:
            before |= Q(is_correct=True)
        position = self.question.answers.filter(before).count()
        return f"{self.question.get_absolute_url()}?page={position // per_page + 1}#answer-{self.pk}"


class Vote(models.Model):
    value = models.SmallIntegerField("Оценка", choices=[(-1, "Дизлайк"), (1, "Лайк")], default=1,
                                     validators=[MinValueValidator(-1), MaxValueValidator(1)])

    class Meta:
        abstract = True


class QuestionLike(Vote):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Вопрос")

    class Meta:
        verbose_name = "лайк вопроса"
        verbose_name_plural = "лайки вопросов"
        constraints = [
            models.UniqueConstraint(fields=["question", "user"], name="unique_question_vote"),
            models.CheckConstraint(condition=Q(value__in=[-1, 1]), name="valid_question_vote_value"),
        ]

    def __str__(self):
        return f"Лайк вопроса №{self.question_id}"


class AnswerLike(Vote):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, verbose_name="Ответ")

    class Meta:
        verbose_name = "лайк ответа"
        verbose_name_plural = "лайки ответов"
        constraints = [
            models.UniqueConstraint(fields=["answer", "user"], name="unique_answer_vote"),
            models.CheckConstraint(condition=Q(value__in=[-1, 1]), name="valid_answer_vote_value"),
        ]

    def __str__(self):
        return f"Лайк ответа №{self.answer_id}"
