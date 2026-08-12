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

# =====================================================
# STK PUSH
# =====================================================

class StkPushAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        # =================================================
        # GET DATA FROM REQUEST
        # =================================================

        student_id = request.data.get("student_id")
        amount = request.data.get("amount")
        phone_number = request.data.get("phone")

        description = (
            request.data.get("description")
            or "School Fees"
        )

        # =================================================
        # VALIDATE REQUIRED FIELDS
        # =================================================

        if not student_id:
            return Response(
                {
                    "success": False,
                    "message": "student_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not amount:
            return Response(
                {
                    "success": False,
                    "message": "amount is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not phone_number:
            return Response(
                {
                    "success": False,
                    "message": "phone is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # GET STUDENT
        # =================================================

        try:

            student = Student.objects.select_related(
                "parent",
                "classroom",
            ).get(
                id=student_id
            )

        except Student.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Student not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # =================================================
        # AUTHORIZE USER
        #
        # Parent:
        #   Can only pay for their own child.
        #
        # Accountant/Admin:
        #   Can pay for any student.
        # =================================================

        user = request.user

        is_parent = (
            getattr(user, "role", None)
            == "PARENT"
        )

        if is_parent:

            if student.parent_id != getattr(
                getattr(user, "parent_profile", None),
                "id",
                None
            ):

                return Response(
                    {
                        "success": False,
                        "message":
                        "You are not authorized to pay fees for this student."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        else:

            # Only authorized staff can make payments
            # for students who are not their children.

            allowed_roles = [
                "SUPER_ADMIN",
                "ACCOUNTANT",
                "ACADEMIC_COORDINATOR",
            ]

            if getattr(user, "role", None) not in allowed_roles:

                return Response(
                    {
                        "success": False,
                        "message":
                        "You are not authorized to make this payment."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # =================================================
        # FIND STUDENT FEE ACCOUNT
        # =================================================

        student_fee = (
            StudentFee.objects
            .select_related(
                "student",
                "fee_structure",
            )
            .filter(
                student=student
            )
            .order_by(
                "-fee_structure__academic_year",
                "-fee_structure__term",
            )
            .first()
        )

        if not student_fee:

            return Response(
                {
                    "success": False,
                    "message":
                    "No fee account exists for this student."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # VALIDATE AMOUNT
        # =================================================

        try:

            amount = int(float(amount))

        except (ValueError, TypeError):

            return Response(
                {
                    "success": False,
                    "message": "Invalid payment amount."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount < 100:

            return Response(
                {
                    "success": False,
                    "message":
                    "Payment amount must be at least KES 100."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # CHECK REMAINING BALANCE
        # =================================================

        if amount > float(student_fee.balance):

            return Response(
                {
                    "success": False,
                    "message": (
                        f"Payment amount cannot exceed "
                        f"the student's fee balance of "
                        f"KES {student_fee.balance}."
                    ),
                    "balance": student_fee.balance,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # NORMALIZE PHONE NUMBER
        # =================================================

        phone_number = (
            str(phone_number)
            .replace(" ", "")
            .replace("-", "")
            .replace("+", "")
        )

        if phone_number.startswith("0"):

            phone_number = (
                "254"
                + phone_number[1:]
            )

        elif phone_number.startswith("7"):

            phone_number = (
                "254"
                + phone_number
            )

        if not phone_number.startswith("2547"):

            return Response(
                {
                    "success": False,
                    "message":
                    "Invalid Kenyan M-Pesa phone number."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # RECEIVED BY
        #
        # Parents don't have accountant_profile.
        # Therefore keep it None for parent payments.
        # =================================================

        accountant = getattr(
            user,
            "accountant_profile",
            None,
        )

        # =================================================
        # CREATE PENDING PAYMENT
        # =================================================

        payment = FeePayment.objects.create(

            student_fee=student_fee,

            amount=amount,

            payment_method=(
                FeePayment.PaymentMethod.MPESA
            ),

            payment_status=(
                FeePayment.PaymentStatus.PENDING
            ),

            receipt_number=(
                f"PENDING-"
                f"{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
            ),

            phone_number=phone_number,

            received_by=accountant,
        )

        # =================================================
        # SEND STK PUSH
        # =================================================

        try:

            response = DarajaService.stk_push(

                phone_number=phone_number,

                amount=amount,

                account_reference=str(
                    student.admission_number
                ),

                transaction_desc=(
                    description[:100]
                    if description
                    else (
                        f"School Fees - "
                        f"{student.first_name} "
                        f"{student.last_name}"
                    )
                ),
            )

        except Exception as e:

            payment.payment_status = (
                FeePayment.PaymentStatus.FAILED
            )

            payment.result_description = str(e)

            payment.save(
                update_fields=[
                    "payment_status",
                    "result_description",
                ]
            )

            return Response(
                {
                    "success": False,
                    "message": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =================================================
        # SAVE SAFARICOM REQUEST IDS
        # =================================================

        payment.merchant_request_id = (
            response.get(
                "MerchantRequestID",
                ""
            )
        )

        payment.checkout_request_id = (
            response.get(
                "CheckoutRequestID",
                ""
            )
        )

        payment.save(
            update_fields=[
                "merchant_request_id",
                "checkout_request_id",
            ]
        )

        # =================================================
        # RESPONSE
        # =================================================

        return Response(
            {
                "success": True,

                "message":
                "STK Push sent successfully.",

                "payment_id":
                payment.id,

                "student_id":
                student.id,

                "student_name":
                (
                    f"{student.first_name} "
                    f"{student.last_name}"
                ),

                "amount":
                payment.amount,

                "merchant_request_id":
                payment.merchant_request_id,

                "checkout_request_id":
                payment.checkout_request_id,

                "customer_message":
                response.get(
                    "CustomerMessage"
                ),
            },
            status=status.HTTP_200_OK,
        )
    

# =====================================================
# MPESA CALLBACK
# =====================================================

class MpesaCallbackAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        data = request.data

        callback = (
            data
            .get("Body", {})
            .get("stkCallback", {})
        )

        checkout_request_id = (
            callback.get("CheckoutRequestID")
        )

        if not checkout_request_id:

            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                    "No CheckoutRequestID."
                }
            )

        # =================================================
        # SAVE CALLBACK
        # =================================================

        MpesaCallbackLog.objects.get_or_create(
            checkout_request_id=checkout_request_id,
            defaults={
                "payload": data,
            }
        )

        # =================================================
        # FIND PAYMENT
        # =================================================

        try:

            payment = FeePayment.objects.get(
                checkout_request_id=checkout_request_id
            )

        except FeePayment.DoesNotExist:

            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                    "Payment not found."
                }
            )

        # =================================================
        # PREVENT DUPLICATE PROCESSING
        # =================================================

        if (
            payment.payment_status
            == FeePayment.PaymentStatus.SUCCESS
        ):

            return Response(
                {
                    "ResultCode": 0,
                    "ResultDesc":
                    "Already processed."
                }
            )

        result_code = callback.get(
            "ResultCode"
        )

        result_desc = callback.get(
            "ResultDesc"
        )

        payment.result_code = str(
            result_code
        )

        payment.result_description = (
            result_desc
        )

        # =================================================
        # SUCCESS
        # =================================================

        if result_code == 0:

            metadata = {}

            items = (
                callback
                .get("CallbackMetadata", {})
                .get("Item", [])
            )

            for item in items:

                name = item.get("Name")

                if name:
                    metadata[name] = item.get(
                        "Value"
                    )

            # ---------------------------------------------
            # M-PESA RECEIPT
            # ---------------------------------------------

            payment.mpesa_receipt = (
                metadata.get(
                    "MpesaReceiptNumber"
                )
            )

            # ---------------------------------------------
            # PHONE
            # ---------------------------------------------

            if metadata.get("PhoneNumber"):

                payment.phone_number = str(
                    metadata.get(
                        "PhoneNumber"
                    )
                )

            # ---------------------------------------------
            # TRANSACTION DATE
            # ---------------------------------------------

            payment.transaction_date = (
                timezone.now()
            )

            # ---------------------------------------------
            # UPDATE PAYMENT + STUDENT FEE
            # ---------------------------------------------

            with transaction.atomic():

                # Lock fee account to prevent
                # simultaneous callbacks/payments
                student_fee = (
                    StudentFee.objects
                    .select_for_update()
                    .get(
                        id=payment.student_fee_id
                    )
                )

                # Only add this payment once
                student_fee.amount_paid = (
                    student_fee.amount_paid
                    + payment.amount
                )

                student_fee.balance = max(
                    student_fee.total_fee
                    - student_fee.amount_paid,
                    0
                )

                student_fee.save(
                    update_fields=[
                        "amount_paid",
                        "balance",
                    ]
                )

                payment.payment_status = (
                    FeePayment.PaymentStatus.SUCCESS
                )

                payment.save()

        # =================================================
        # FAILED / CANCELLED
        # =================================================

        else:

            payment.payment_status = (
                FeePayment.PaymentStatus.FAILED
            )

            payment.save(
                update_fields=[
                    "result_code",
                    "result_description",
                    "payment_status",
                ]
            )

        # =================================================
        # ALWAYS ACKNOWLEDGE SAFARICOM
        # =================================================

        return Response(
            {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
        )