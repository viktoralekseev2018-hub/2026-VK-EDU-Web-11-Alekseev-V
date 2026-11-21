from itertools import batched
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.test.utils import override_settings
from faker import Faker

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag


BATCH = 2000


def insert(model, rows):
    for batch in batched(rows, BATCH):
        yield from model.objects.bulk_create(batch, batch_size=BATCH)


def insert_ids(model, rows):
    return [row.pk for row in insert(model, rows)]


def insert_all(model, rows):
    for _ in insert(model, rows):
        pass


class Command(BaseCommand):
    help = "Добавить пользователей, вопросы, ответы, теги и лайки пропорционально ratio."

    def add_arguments(self, parser):
        parser.add_argument("ratio", type=int)

    @override_settings(DEBUG=False)
    @transaction.atomic
    def handle(self, *args, ratio, **options):
        if ratio < 2:
            raise CommandError("Нужны минимум два пользователя для 200 уникальных оценок на каждые 110 публикаций.")
        # Проверяем внешние ключи по мере вставки, чтобы не копить миллионы отложенных проверок.
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        fake = Faker("ru_RU")
        prefix = uuid4().hex[:16]
        User = get_user_model()
        users = insert_ids(User, (User(username=f"demo_{prefix}_{i}", first_name=fake.first_name(),
                                       last_name=fake.last_name(), password="!")
                                  for i in range(ratio)))
        insert_all(Profile, (Profile(user_id=user) for user in users))
        tags = insert_ids(Tag, (Tag(name=f"{fake.word()}-{prefix}-{i}") for i in range(ratio)))
        # Банк фраз позволяет заполнять миллионы строк без миллиона вызовов Faker.
        texts = [fake.paragraph(nb_sentences=3) for _ in range(512)]
        titles = [fake.sentence(nb_words=7).rstrip(".") + "?" for _ in range(512)]

        question_ids = insert_ids(Question, (
            Question(author_id=users[i % ratio], title=fake.random_element(titles),
                     text=fake.random_element(texts)) for i in range(10 * ratio)
        ))
        question_tag = Question.tags.through
        insert_all(question_tag, (
            question_tag(question_id=pk, tag_id=tags[i % ratio])
            for i, pk in enumerate(question_ids)
        ))
        insert_all(QuestionLike, (
            QuestionLike(question_id=pk, user_id=users[(i + j) % ratio])
            for i, pk in enumerate(question_ids) if i % 2 == 0 for j in range(2)
        ))
        for indexes in batched(range(100 * ratio), BATCH):
            answers = Answer.objects.bulk_create([
                Answer(question_id=question_ids[i // 10], author_id=users[i % ratio],
                       text=fake.random_element(texts), is_correct=i % 10 == 0) for i in indexes
            ])
            insert_all(AnswerLike, (
                AnswerLike(answer_id=answer.pk, user_id=users[(i + j) % ratio])
                for i, answer in zip(indexes, answers)
                for j in range(1 if i % 10 == 0 else 2)
            ))
        self.stdout.write(self.style.SUCCESS(
            f"Добавлено пользователей: {ratio}, тегов: {ratio}, вопросов: {10 * ratio}, "
            f"ответов: {100 * ratio}, оценок: {200 * ratio}."
        ))
