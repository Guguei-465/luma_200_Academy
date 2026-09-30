from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    DarajaTokenAPIView,
    MpesaCallbackAPIView,
    ReceiptByNumberAPIView,
    StkPushAPIView,
    FeeStructureViewSet,
    StudentFeeViewSet,
    FeePaymentViewSet,
    AccountantDashboardAPIView,
    StudentFeeDashboardAPIView,
)

router = DefaultRouter()

# Fee Structures
router.register(
    r"fee-structures",
    FeeStructureViewSet,
    basename="fee-structure",
)

# Student Fees
router.register(
    r"student-fees",
    StudentFeeViewSet,
    basename="student-fee",
)

# Payments
router.register(
    r"payments",
    FeePaymentViewSet,
    basename="fee-payment",
)

urlpatterns = [
    path("daraja/token/", DarajaTokenAPIView.as_view(), name="daraja-token"),
    path("payments/stk-push/", StkPushAPIView.as_view(), name="stk-push"),
    path("dashboard/", AccountantDashboardAPIView.as_view(), name="accountant-dashboard"),
    path("student/<int:student_id>/", StudentFeeDashboardAPIView.as_view(), name="student-fee-dashboard"),
    path("mpesa/callback/", MpesaCallbackAPIView.as_view(), name="mpesa-callback"),
    path("receipt/<str:receipt_number>/", ReceiptByNumberAPIView.as_view(), name="receipt-by-number"),
    
    # Auto-generated router endpoints
    path("", include(router.urls)),
]