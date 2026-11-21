from functools import wraps

from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import resolve_url

from .forms import CorrectAnswerForm, VoteForm
from .models import Answer, AnswerLike, Question, QuestionLike


def json_post(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.method != "POST":
            return JsonResponse({"error": "Используйте POST."}, status=405, headers={"Allow": "POST"})
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Войдите, чтобы выполнить это действие.",
                                 "login_url": resolve_url("core:login")}, status=401)
        return view(request, *args, **kwargs)
    return wrapped


def invalid_form(form):
    return JsonResponse({"error": "Проверьте параметры запроса.", "fields": form.errors.get_json_data()},
                        status=400)


@transaction.atomic
def change_vote(request, target_id, model, vote_model, relation):
    form = VoteForm(request.POST)
    if not form.is_valid():
        return invalid_form(form)
    target = model.objects.select_for_update().filter(pk=target_id).first()
    if target is None:
        return JsonResponse({"error": "Публикация не найдена."}, status=404)

    votes = vote_model.objects.filter(**{relation: target})
    value = form.cleaned_data["value"]
    vote, created = votes.get_or_create(user=request.user, defaults={"value": value}, **{relation: target})
    duplicate = not created and vote.value == value
    if not created and not duplicate:
        vote.value = value
        vote.save(update_fields=["value"])

    result = {"rating": votes.aggregate(total=Sum("value", default=0))["total"], "my_vote": value}
    if duplicate:
        result["error"] = "Вы уже поставили эту оценку."
    return JsonResponse(result, status=409 if duplicate else 200)


@json_post
def question_vote(request, question_id):
    return change_vote(request, question_id, Question, QuestionLike, "question")


@json_post
def answer_vote(request, answer_id):
    return change_vote(request, answer_id, Answer, AnswerLike, "answer")


@json_post
@transaction.atomic
def correct_answer(request):
    form = CorrectAnswerForm(request.POST)
    if not form.is_valid():
        return invalid_form(form)
    question = Question.objects.select_for_update().filter(pk=form.cleaned_data["question_id"]).first()
    if question is None:
        return JsonResponse({"error": "Вопрос не найден."}, status=404)
    if question.author_id != request.user.pk:
        return JsonResponse({"error": "Правильный ответ может выбрать только автор вопроса."}, status=403)

    answer = question.answers.filter(pk=form.cleaned_data["answer_id"]).first()
    if answer is None:
        return JsonResponse({"error": "У этого вопроса нет такого ответа."}, status=404)
    selected = form.cleaned_data["selected"]
    previous = question.answers.filter(is_correct=True).exclude(pk=answer.pk)
    cleared = list(previous.values_list("pk", flat=True)) if selected else []
    result = {"answer_id": answer.pk, "selected": selected, "cleared": cleared}
    if answer.is_correct == selected and not cleared:
        result["error"] = "Эта отметка уже сохранена."
        return JsonResponse(result, status=409)
    if cleared:
        previous.update(is_correct=False)
    answer.is_correct = selected
    answer.save(update_fields=["is_correct"])
    return JsonResponse(result)
