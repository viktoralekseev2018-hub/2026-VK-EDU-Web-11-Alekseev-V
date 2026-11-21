from django import forms
from django.contrib import admin
from django.db.models import Exists, OuterRef

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0

    # Поле ID сохраняет проверку ForeignKey без отдельных запросов за подписями.
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            kwargs["widget"] = forms.NumberInput
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "created_at")
    search_fields = ("title", "author__username")
    list_filter = ("created_at",)
    autocomplete_fields = ("author", "tags")
    list_select_related = ("author",)
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "text_preview", "question", "author", "is_correct")
    search_fields = ("text", "question__title", "author__username")
    list_filter = ("is_correct", "created_at")
    autocomplete_fields = ("question", "author")
    list_select_related = ("question", "author")

    @admin.display(description="Текст")
    def text_preview(self, obj):
        return str(obj)


class TagUsageFilter(admin.SimpleListFilter):
    title = "Использование"
    parameter_name = "used"

    def lookups(self, request, model_admin):
        return (("yes", "Есть вопросы"), ("no", "Без вопросов"))

    def queryset(self, request, queryset):
        used = Exists(Question.tags.through.objects.filter(tag_id=OuterRef("pk")))
        if self.value() == "yes":
            return queryset.filter(used)
        if self.value() == "no":
            return queryset.filter(~used)
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    list_filter = (TagUsageFilter,)


class LikeAdmin(admin.ModelAdmin):
    list_filter = ("user__is_active",)


@admin.register(QuestionLike)
class QuestionLikeAdmin(LikeAdmin):
    list_display = ("id", "question", "user")
    search_fields = ("question__title", "user__username")
    autocomplete_fields = ("question", "user")
    list_select_related = ("question", "user")


@admin.register(AnswerLike)
class AnswerLikeAdmin(LikeAdmin):
    list_display = ("id", "answer", "user")
    search_fields = ("answer__text", "user__username")
    autocomplete_fields = ("answer", "user")
    list_select_related = ("answer", "user")
