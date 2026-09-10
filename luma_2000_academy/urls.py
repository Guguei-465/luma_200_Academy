"""
URL configuration for luma_2000_academy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.http import JsonResponse
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


# ============================================================
# ROOT / HOME
# ============================================================

def home(request):
    return JsonResponse({
        "message": "Luma Academy API is running",
        "status": "success"
    })


# ============================================================
# URL PATTERNS
# ============================================================

urlpatterns = [

    # --------------------------------------------------------
    # ROOT
    # --------------------------------------------------------

    path("", home, name="home"),

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    path("admin/", admin.site.urls),

    # --------------------------------------------------------
    # API DOCUMENTATION
    # --------------------------------------------------------

    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema"
    ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui"
    ),

    # --------------------------------------------------------
    # ACCOUNTS
    # --------------------------------------------------------

    path(
        "api/accounts/",
        include("accounts.urls")
    ),

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

    path(
        "api/dashboard/",
        include("dashboard.urls")
    ),

    # --------------------------------------------------------
    # STUDENTS
    # --------------------------------------------------------

    path(
        "api/students/",
        include("students.urls")
    ),

    # --------------------------------------------------------
    # CLASSES
    # --------------------------------------------------------

    path(
        "api/classes/",
        include("classes.urls")
    ),

    # --------------------------------------------------------
    # SUBJECTS
    # --------------------------------------------------------

    path(
        "api/subjects/",
        include("subjects.urls")
    ),

    # --------------------------------------------------------
    # ASSIGNMENTS
    # --------------------------------------------------------

    path(
        "api/assignments/",
        include("assignments.urls")
    ),

    # --------------------------------------------------------
    # TIMETABLE
    # --------------------------------------------------------

    path(
        "api/timetable/",
        include("timetable.urls")
    ),

    # --------------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------------

    path(
        "api/attendance/",
        include("attendance.urls")
    ),

    # --------------------------------------------------------
    # EXAMS
    # --------------------------------------------------------

    path(
        "api/exams/",
        include("exams.urls")
    ),

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    path(
        "api/results/",
        include("results.urls")
    ),

    # --------------------------------------------------------
    # REPORTS
    # --------------------------------------------------------

    path(
        "api/reports/",
        include("reports.urls")
    ),

    # --------------------------------------------------------
    # FEES
    # --------------------------------------------------------

    path(
        "api/fees/",
        include("fees.urls")
    ),

    # --------------------------------------------------------
    # ANNOUNCEMENTS
    # --------------------------------------------------------

    path(
        "api/anouncements/",
        include("anouncements.urls")
    ),

    # --------------------------------------------------------
    # PARENTS
    # --------------------------------------------------------

    path(
        "api/parents/",
        include("parents.urls")
    ),

    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    path(
        "api/notifiations/",
        include("notifiations.urls")
    ),
]