from questions.models import Question, Tag


def sidebar(request):
    return {"popular_tags": Tag.objects.popular(), "best_members": Question.objects.top_authors()}
