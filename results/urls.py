from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    GradeScaleViewSet,
    AssessmentTypeViewSet,
    AssessmentViewSet,
    LearningOutcomeViewSet,
    ResultSubmissionViewSet,
    ResultViewSet,
    StudentReportCardAPIView,
    StudentResultViewSet,
    StudentTermResultViewSet,
    ReportCommentViewSet,
)

router = DefaultRouter()

router.register(
    r"grade-scales",
    GradeScaleViewSet,
    basename="grade-scale",
)

router.register(
    r"assessment-types",
    AssessmentTypeViewSet,
    basename="assessment-type",
)

router.register(
    r"assessments",
    AssessmentViewSet,
    basename="assessment",
)

router.register(
    r"learning-outcomes",
    LearningOutcomeViewSet,
    basename="learning-outcome",
)

router.register(
    r"result-submissions",
    ResultSubmissionViewSet,
    basename="result-submission",
)

router.register(
    r"results",
    ResultViewSet,
    basename="result",
)

router.register(
    r"student-results",
    StudentResultViewSet,
    basename="student-result",
)

router.register(
    r"student-term-results",
    StudentTermResultViewSet,
    basename="student-term-result",
)

router.register(
    r"report-comments",
    ReportCommentViewSet,
    basename="report-comment",
)


urlpatterns = [
    path("", include(router.urls)),
    path(
        "report-card/<int:student_id>/<str:academic_year>/<str:term>/",
        StudentReportCardAPIView.as_view(),
        name="student-report-card",
    ),
]