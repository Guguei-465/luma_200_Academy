from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DarajaTokenAPIView, MpesaCallbackAPIView, StkPushAPIView
from .views import (
    FeeStructureViewSet,
    StudentFeeViewSet,
    FeePaymentViewSet,
    AccountantDashboardAPIView,
    StudentFeeDashboardAPIView,
)

router = DefaultRouter()

router.register(
    r"fee-structures",
    FeeStructureViewSet,
    basename="fee-structure",
)

router.register(
    r"student-fees",
    StudentFeeViewSet,
    basename="student-fee",
)

router.register(
    r"payments",
    FeePaymentViewSet,
    basename="fee-payment",
)

urlpatterns = [
    path(
        "daraja/token/",
        DarajaTokenAPIView.as_view(),
        name="daraja-token",
    ),

    path(
        "payments/stk-push/",
        StkPushAPIView.as_view(),
        name="stk-push",
    ),

    path(
        "dashboard/",
        AccountantDashboardAPIView.as_view(),
        name="accountant-dashboard",
    ),

    path(
        "student/<int:student_id>/",
        StudentFeeDashboardAPIView.as_view(),
        name="student-fee-dashboard",
    ),

    path(
        "mpesa/callback/",
        MpesaCallbackAPIView.as_view(),
        name="mpesa-callback",
    ),

    

    path("", include(router.urls)),
]