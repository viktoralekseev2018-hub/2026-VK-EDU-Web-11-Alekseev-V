from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from core.pagination import paginate
from .forms import AnswerForm, AskForm
from .models import Answer, Question, Tag

ANSWERS_PER_PAGE = 5


def question_list(request, queryset, template, **context):
    query = request.GET.get("q", "").strip()[:100]
    page = paginate(queryset.search(query), request)
    return render(request, template, {"page_obj": page, "search_query": query, **context})


@require_GET
def index(request):
    return question_list(request, Question.objects.newest(), "questions/index.html", list_mode="new")


@require_GET
def hot(request):
    return question_list(request, Question.objects.popular(), "questions/hot.html", list_mode="hot")


@require_GET
def tag(request, tag):
    selected = get_object_or_404(Tag, name=tag)
    return question_list(request, Question.objects.by_tag(selected), "questions/tag.html",
                         tag_name=selected.name)


def render_question(request, item, form):
    answers = Answer.objects.for_question(item)
    page = paginate(answers, request, per_page=ANSWERS_PER_PAGE)
    return render(request, "questions/question.html", {"question": item, "page_obj": page, "form": form})


@login_required
def submit_answer(request, question_id):
    item = get_object_or_404(Question.objects.cards(), pk=question_id)
    form = AnswerForm(request.POST)
    if form.is_valid():
        answer = form.save(question=item, author=request.user)
        return redirect(answer.url_on_page(ANSWERS_PER_PAGE))
    return render_question(request, item, form)


@require_http_methods(["GET", "POST"])
def question(request, question_id):
    if request.method == "POST":
        return submit_answer(request, question_id)
    item = get_object_or_404(Question.objects.cards(), pk=question_id)
    return render_question(request, item, AnswerForm())


@login_required
@require_http_methods(["GET", "POST"])
def ask(request):
    form = AskForm(request.POST if request.method == "POST" else None)
    if form.is_valid():
        return redirect(form.save(author=request.user))
    return render(request, "questions/ask.html", {"form": form})
