from django.urls import path

from . import ajax, views

app_name = "questions"
urlpatterns = [
    path("", views.index, name="index"),
    path("hot/", views.hot, name="hot"),
    path("tag/<str:tag>/", views.tag, name="tag"),
    path("question/<int:question_id>/", views.question, name="question"),
    path("ask/", views.ask, name="ask"),
    path("ajax/questions/<int:question_id>/vote/", ajax.question_vote, name="ajax_question_vote"),
    path("ajax/answers/<int:answer_id>/vote/", ajax.answer_vote, name="ajax_answer_vote"),
    path("ajax/answers/correct/", ajax.correct_answer, name="ajax_correct_answer"),
]
