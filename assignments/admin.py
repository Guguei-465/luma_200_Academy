from django.contrib import admin
from django.contrib import admin
from .models import TeacherAssignment


# Register your models here.
@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        "teacher",
        "classroom",
        "subject",
        "academic_year",
        "term",
        "is_class_teacher",
        "is_active",
    )

    list_filter = (
        "academic_year",
        "term",
        "is_class_teacher",
        "is_active",
    )

    search_fields = (
        "teacher__user__first_name",
        "teacher__user__last_name",
        "subject__name",
        "classroom__grade",
    )

    ordering = (
        "-academic_year",
        "term",
    )