from django.conf import settings
from django.db import models
from django.db.models import Count, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone


def related_count(model, foreign_key):
    rows = model.objects.filter(**{foreign_key: OuterRef("pk")}).order_by().values(foreign_key)
    return Coalesce(Subquery(rows.annotate(total=Count("pk")).values("total")), 0)


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
    def cards(self):
        return self.select_related("author__profile").prefetch_related("tags").annotate(
            rating=related_count(QuestionLike, "question_id"),
            answers_count=related_count(Answer, "question_id"),
        )

    def newest(self):
        return self.cards().order_by("-created_at", "-pk")

    def popular(self):
        return self.cards().order_by("-rating", "-pk")

    def by_tag(self, tag):
        return self.newest().filter(tags=tag)

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
    def for_question(self, question):
        return self.filter(question=question).select_related("author__profile").annotate(
            rating=related_count(AnswerLike, "answer_id"),
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


class QuestionLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Вопрос")

    class Meta:
        verbose_name = "лайк вопроса"
        verbose_name_plural = "лайки вопросов"
        constraints = [models.UniqueConstraint(fields=["question", "user"], name="unique_question_vote")]

    def __str__(self):
        return f"Лайк вопроса №{self.question_id}"


class AnswerLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, verbose_name="Ответ")

    class Meta:
        verbose_name = "лайк ответа"
        verbose_name_plural = "лайки ответов"
        constraints = [models.UniqueConstraint(fields=["answer", "user"], name="unique_answer_vote")]

    def __str__(self):
        return f"Лайк ответа №{self.answer_id}"
