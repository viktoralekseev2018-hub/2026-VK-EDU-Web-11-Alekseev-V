from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods

from core.pagination import paginate
from core.views import DEMO_MESSAGE, render_form_page
from .forms import AnswerForm, AskForm
from .models import Answer, Question, Tag


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
    return question_list(request, Question.objects.by_tag(selected), "questions/tag.html", tag_name=selected.name)


@require_http_methods(["GET", "POST"])
def question(request, question_id):
    item = get_object_or_404(Question.objects.cards(), pk=question_id)
    page = paginate(Answer.objects.for_question(item), request, per_page=5)
    form = AnswerForm(request.POST if request.method == "POST" else None)
    return render(request, "questions/question.html", {"question": item, "page_obj": page, "form": form,
                  "form_action": item.get_absolute_url(), "demo_message": DEMO_MESSAGE if form.is_valid() else ""})


@require_http_methods(["GET", "POST"])
def ask(request):
    return render_form_page(request, "questions/ask.html", AskForm)
