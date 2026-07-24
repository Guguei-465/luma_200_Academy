from django.db.models import Sum
from .services import DarajaService
from .serializers import StkPushSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from fees.services import DarajaService
from students.models import Student
from django.db import transaction
from rest_framework.permissions import AllowAny
from .models import (
    FeeStructure,
    StudentFee,
    FeePayment,
    MpesaCallbackLog, 
)
from .serializers import (
    FeeStructureSerializer,
    StudentFeeSerializer,
    FeePaymentSerializer,
)

from .permissions import (
    IsSuperAdminOrAccountant,
    IsSuperAdminAccountantOrAcademicCoordinator,
)


# =====================================================
# Fee Structure
# =====================================================
class FeeStructureViewSet(viewsets.ModelViewSet):

    queryset = FeeStructure.objects.all().order_by(
        "-academic_year",
        "term",
    )

    serializer_class = FeeStructureSerializer
    permission_classes = [
        IsAuthenticated,
        IsSuperAdminOrAccountant,
    ]

    @action(detail=True, methods=["post"])
    def generate_accounts(self, request, pk=None):

        fee_structure = self.get_object()

        students = Student.objects.filter(
            classroom=fee_structure.classroom
        )

        created = 0
        skipped = 0

        for student in students:

            _, was_created = StudentFee.objects.get_or_create(

                student=student,
                fee_structure=fee_structure,

                defaults={
                    "total_fee": fee_structure.total_fee,
                    "amount_paid": 0,
                    "balance": fee_structure.total_fee,
                }
            )

            if was_created:
                created += 1
            else:
                skipped += 1

        return Response(
            {
                "message": "Fee accounts generated successfully.",
                "created": created,
                "skipped": skipped,
            },
            status=status.HTTP_200_OK,
        )


# =====================================================
# Student Fee Accounts
# =====================================================
class StudentFeeViewSet(viewsets.ModelViewSet):

    queryset = StudentFee.objects.select_related(
        "student",
        "fee_structure",
        "fee_structure__classroom",
    ).order_by(
        "student__first_name",
    )

    serializer_class = StudentFeeSerializer

    permission_classes = [
        IsAuthenticated,
        IsSuperAdminOrAccountant,
    ]


# =====================================================
# Fee Payments
# =====================================================
class FeePaymentViewSet(viewsets.ModelViewSet):

    queryset = FeePayment.objects.select_related(
        "student_fee",
        "student_fee__student",
        "received_by",
    ).order_by(
        "-payment_date",
    )

    serializer_class = FeePaymentSerializer

    permission_classes = [
        IsAuthenticated,
        IsSuperAdminOrAccountant,
    ]

    @action(detail=False, methods=["get"])
    def successful(self, request):

        queryset = self.get_queryset().filter(
            payment_status=FeePayment.PaymentStatus.SUCCESS
        )

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def pending(self, request):

        queryset = self.get_queryset().filter(
            payment_status=FeePayment.PaymentStatus.PENDING
        )

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)


# =====================================================
# Accountant Dashboard
# =====================================================
class AccountantDashboardAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsSuperAdminOrAccountant,
    ]

    def get(self, request):

        total_expected = (
            StudentFee.objects.aggregate(
                total=Sum("total_fee")
            )["total"]
            or 0
        )

        total_paid = (
            StudentFee.objects.aggregate(
                total=Sum("amount_paid")
            )["total"]
            or 0
        )

        total_balance = (
            StudentFee.objects.aggregate(
                total=Sum("balance")
            )["total"]
            or 0
        )

        total_payments = FeePayment.objects.count()

        return Response(
            {
                "students": StudentFee.objects.count(),
                "payments": total_payments,
                "total_expected": total_expected,
                "total_paid": total_paid,
                "total_balance": total_balance,
            }
        )


# =====================================================
# Student Fee Dashboard
# =====================================================
class StudentFeeDashboardAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsSuperAdminAccountantOrAcademicCoordinator,
    ]

    def get(self, request, student_id):

        queryset = StudentFee.objects.filter(
            student_id=student_id
        )

        if not queryset.exists():

            return Response(
                {
                    "message":
                    "No fee records found for this student."
                },
                status=status.HTTP_200_OK,
            )

        serializer = StudentFeeSerializer(
            queryset,
            many=True,
        )

        return Response(serializer.data)
    

# =====================================================
# Test Daraja Connection
# =====================================================

class DarajaTokenAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsSuperAdminOrAccountant,
    ]

    def get(self, request):

        try:

            token = DarajaService.get_access_token()

            return Response(
                {
                    "success": True,
                    "access_token": token,
                }
            )

        except Exception as e:

            return Response(
                {
                    "success": False,
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

# =====================================================
# STK Push
# =====================================================

class StkPushAPIView(APIView):
    permission_classes = [IsSuperAdminOrAccountant]

    def post(self, request):

        serializer = StkPushSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        student_fee = serializer.validated_data["student_fee"]
        phone_number = serializer.validated_data["phone_number"]
        amount = serializer.validated_data["amount"]

        accountant = getattr(
            request.user,
            "accountant_profile",
            None,
        )

        payment = FeePayment.objects.create(
            student_fee=student_fee,
            amount=amount,
            payment_method=FeePayment.PaymentMethod.MPESA,
            payment_status=FeePayment.PaymentStatus.PENDING,
            receipt_number=f"PENDING-{timezone.now().strftime('%Y%m%d%H%M%S%f')}",
            phone_number=phone_number,
            received_by=accountant,
        )

        try:
            response = DarajaService.stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference=str(student_fee.student.admission_number),
                transaction_desc=(
                    f"School Fees - "
                    f"{student_fee.student.first_name} "
                    f"{student_fee.student.last_name}"
                ),
            )

        except Exception as e:

            payment.payment_status = FeePayment.PaymentStatus.FAILED
            payment.result_description = str(e)
            payment.save()

            return Response(
                {
                    "success": False,
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
                
        payment.merchant_request_id = response.get(
            "MerchantRequestID",
            ""
        )

        payment.checkout_request_id = response.get(
            "CheckoutRequestID",
            ""
        )

        payment.save()

        return Response(
            {
                "success": True,
                "message": "STK Push sent successfully.",
                "payment_id": payment.id,
                "merchant_request_id": payment.merchant_request_id,
                "checkout_request_id": payment.checkout_request_id,
                "customer_message": response.get(
                    "CustomerMessage"
                ),
            },
            status=status.HTTP_200_OK,
        )
    

class MpesaCallbackAPIView(APIView):
    """
    Receives STK Push callback from Safaricom.
    """

    permission_classes = [AllowAny]

    def post(self, request):

        data = request.data

        callback = data.get("Body", {}).get("stkCallback", {})

        checkout_request_id = callback.get("CheckoutRequestID")

        if not checkout_request_id:
            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc": "No CheckoutRequestID."
                }
            )

        # Save callback payload
        MpesaCallbackLog.objects.get_or_create(
            checkout_request_id=checkout_request_id,
            defaults={
                "payload": data,
            }
        )

        try:
            payment = FeePayment.objects.get(
                checkout_request_id=checkout_request_id
            )

        except FeePayment.DoesNotExist:
            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc": "Payment not found."
                }
            )

        # Prevent duplicate processing
        if payment.payment_status == FeePayment.PaymentStatus.SUCCESS:
            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc": "Already processed."
                }
            )

        result_code = callback.get("ResultCode")
        result_desc = callback.get("ResultDesc")

        payment.result_code = str(result_code)
        payment.result_description = result_desc

        if result_code == 0:

            metadata = {}

            for item in callback.get(
                "CallbackMetadata",
                {}
            ).get(
                "Item",
                []
            ):

                metadata[item["Name"]] = item.get("Value")

            payment.mpesa_receipt = metadata.get(
                "MpesaReceiptNumber"
            )

            payment.phone_number = str(
                metadata.get(
                    "PhoneNumber",
                    ""
                )
            )

            payment.transaction_date = timezone.now()

            payment.payment_status = (
                FeePayment.PaymentStatus.SUCCESS
            )

            with transaction.atomic():

                payment.save()

                student_fee = payment.student_fee

                student_fee.amount_paid += payment.amount

                student_fee.save()

        else:

            payment.payment_status = (
                FeePayment.PaymentStatus.FAILED
            )

            payment.save()

        return Response(
            {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
        )