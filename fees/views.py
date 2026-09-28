from django.db.models import Sum, Count, Q
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import DarajaService
from students.models import Student
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
)

# =====================================================
# FEE STRUCTURE
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
                },
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
# STUDENT FEE ACCOUNTS — WITH FILTERS
# =====================================================
class StudentFeeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Fee accounts with filtering by class & payment status.
    Query params:
      - classroom: "all" or classroom ID
      - status: "all" / "paid" / "unpaid"
    SUPER_ADMIN / ACCOUNTANT / ACADEMIC_COORDINATOR:
        Can view all fee records.
    PARENT:
        Can only view fee records belonging to their children.
    """
    serializer_class = StudentFeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        classroom_id = self.request.query_params.get("classroom")
        status_filter = self.request.query_params.get("status")

        # Base queryset
        if getattr(user, "role", None) in [
            "SUPER_ADMIN", "ACCOUNTANT", "ACADEMIC_COORDINATOR",
        ]:
            qs = StudentFee.objects.select_related(
                "student", "fee_structure", "fee_structure__classroom"
            )
        elif getattr(user, "role", None) == "PARENT":
            parent_profile = getattr(user, "parent_profile", None)
            if not parent_profile:
                return StudentFee.objects.none()
            qs = StudentFee.objects.filter(
                student__parent=parent_profile
            ).select_related(
                "student", "fee_structure", "fee_structure__classroom"
            )
        else:
            return StudentFee.objects.none()

        # Apply classroom filter
        if classroom_id and classroom_id != "all" and classroom_id is not None:
            qs = qs.filter(fee_structure__classroom_id=classroom_id)

        # Apply payment status filter
        if status_filter == "paid":
            qs = qs.filter(amount_paid__gt=0)
        elif status_filter == "unpaid":
            qs = qs.filter(amount_paid=0)

        return qs.order_by("student__first_name")

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Return paid/unpaid counts + totals per class & overall"""
        user = request.user
        classroom_id = request.query_params.get("classroom")

        if getattr(user, "role", None) not in [
            "SUPER_ADMIN", "ACCOUNTANT", "ACADEMIC_COORDINATOR",
        ]:
            return Response(
                {"detail": "Not authorized"},
                status=status.HTTP_403_FORBIDDEN,
            )

        qs = StudentFee.objects.all()
        if classroom_id and classroom_id != "all":
            qs = qs.filter(fee_structure__classroom_id=classroom_id)

        # Overall totals
        overall = qs.aggregate(
            total_students=Count("student", distinct=True),
            paid_students=Count("student", filter=Q(amount_paid__gt=0), distinct=True),
            unpaid_students=Count("student", filter=Q(amount_paid=0), distinct=True),
            total_fee=Sum("total_fee"),
            total_paid=Sum("amount_paid"),
            total_balance=Sum("balance"),
        )

        # Per-class breakdown
        per_class = qs.values(
            "fee_structure__classroom__id",
            "fee_structure__classroom__name",
        ).annotate(
            total_students=Count("student", distinct=True),
            paid_students=Count("student", filter=Q(amount_paid__gt=0), distinct=True),
            unpaid_students=Count("student", filter=Q(amount_paid=0), distinct=True),
            total_fee=Sum("total_fee"),
            total_paid=Sum("amount_paid"),
            total_balance=Sum("balance"),
        ).order_by("fee_structure__classroom__name")

        return Response({
            "overall": overall,
            "per_class": per_class,
        })

# =====================================================
# STUDENT FEE DASHBOARD
# =====================================================
class StudentFeeDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        user = request.user
        try:
            student = Student.objects.select_related(
                "parent", "classroom"
            ).get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {"success": False, "message": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        role = getattr(user, "role", None)
        allowed_staff_roles = [
            "SUPER_ADMIN", "ACCOUNTANT", "ACADEMIC_COORDINATOR",
        ]

        if role == "PARENT":
            parent_profile = getattr(user, "parent_profile", None)
            if not parent_profile or student.parent_id != parent_profile.id:
                return Response(
                    {"success": False, "message": "Not authorized to view this student's fees."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif role not in allowed_staff_roles:
            return Response(
                {"success": False, "message": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN,
            )

        fee_accounts = StudentFee.objects.filter(
            student=student
        ).select_related(
            "student", "fee_structure", "fee_structure__classroom"
        ).order_by(
            "-fee_structure__academic_year", "-fee_structure__term"
        )

        serializer = StudentFeeSerializer(fee_accounts, many=True)

        total_fee = sum(float(f.total_fee) for f in fee_accounts)
        total_paid = sum(float(f.amount_paid) for f in fee_accounts)
        total_balance = sum(float(f.balance) for f in fee_accounts)

        classroom_name = None
        if student.classroom:
            classroom_name = (
                getattr(student.classroom, "name", None)
                or getattr(student.classroom, "class_name", None)
                or str(student.classroom)
            )

        return Response({
            "success": True,
            "student": {
                "id": student.id,
                "admission_number": student.admission_number,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "classroom": classroom_name,
            },
            "summary": {
                "total_fee": total_fee,
                "total_paid": total_paid,
                "total_balance": total_balance,
            },
            "fee_accounts": serializer.data,
        })

# =====================================================
# FEE PAYMENTS
# =====================================================
class FeePaymentViewSet(viewsets.ModelViewSet):
    queryset = FeePayment.objects.select_related(
        "student_fee", "student_fee__student", "received_by"
    ).order_by("-payment_date")
    serializer_class = FeePaymentSerializer
    permission_classes = [
        IsAuthenticated,
        IsSuperAdminOrAccountant,
    ]

    def perform_create(self, serializer):
        accountant_profile = getattr(
            self.request.user, "accountant_profile", None
        )
        serializer.save(received_by=accountant_profile)

    @action(detail=False, methods=["get"])
    def successful(self, request):
        qs = self.get_queryset().filter(
            payment_status=FeePayment.PaymentStatus.SUCCESS
        )
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        qs = self.get_queryset().filter(
            payment_status=FeePayment.PaymentStatus.PENDING
        )
        return Response(self.get_serializer(qs, many=True).data)

# =====================================================
# ACCOUNTANT DASHBOARD
# =====================================================
class AccountantDashboardAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdminOrAccountant,
    ]

    def get(self, request):
        total_expected = StudentFee.objects.aggregate(
            total=Sum("total_fee")
        )["total"] or 0
        total_paid = StudentFee.objects.aggregate(
            total=Sum("amount_paid")
        )["total"] or 0
        total_balance = StudentFee.objects.aggregate(
            total=Sum("balance")
        )["total"] or 0
        total_payments = FeePayment.objects.count()

        return Response({
            "students": StudentFee.objects.count(),
            "payments": total_payments,
            "total_expected": total_expected,
            "total_paid": total_paid,
            "total_balance": total_balance,
        })

# =====================================================
# DARAJA TOKEN
# =====================================================
class DarajaTokenAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdminOrAccountant]

    def get(self, request):
        try:
            return Response({
                "success": True,
                "access_token": DarajaService.get_access_token(),
            })
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

# =====================================================
# STK PUSH
# =====================================================
class StkPushAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        student_id = request.data.get("student_id")
        amount = request.data.get("amount")
        phone_number = request.data.get("phone")
        description = request.data.get("description") or "School Fees"

        if not student_id:
            return Response(
                {"success": False, "message": "student_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not amount:
            return Response(
                {"success": False, "message": "amount is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not phone_number:
            return Response(
                {"success": False, "message": "phone is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student = Student.objects.select_related(
                "parent", "classroom"
            ).get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {"success": False, "message": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        is_parent = getattr(user, "role", None) == "PARENT"
        if is_parent:
            parent_profile = getattr(user, "parent_profile", None)
            if not parent_profile or student.parent_id != parent_profile.id:
                return Response(
                    {"success": False, "message": "Not authorized to pay for this student."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            if getattr(user, "role", None) not in [
                "SUPER_ADMIN", "ACCOUNTANT", "ACADEMIC_COORDINATOR",
            ]:
                return Response(
                    {"success": False, "message": "Not authorized."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        student_fee = StudentFee.objects.select_related(
            "student", "fee_structure"
        ).filter(student=student).order_by(
            "-fee_structure__academic_year", "-fee_structure__term"
        ).first()

        if not student_fee:
            return Response(
                {"success": False, "message": "No fee account found for this student."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = int(float(amount))
        except (ValueError, TypeError):
            return Response(
                {"success": False, "message": "Invalid payment amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if amount < 100:
            return Response(
                {"success": False, "message": "Payment must be at least KES 100."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if amount > float(student_fee.balance):
            return Response(
                {
                    "success": False,
                    "message": f"Amount exceeds balance of KES {student_fee.balance}.",
                    "balance": student_fee.balance,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone_number = str(phone_number).replace(" ", "").replace("-", "").replace("+", "")
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif phone_number.startswith("7"):
            phone_number = "254" + phone_number
        if not phone_number.startswith("2547"):
            return Response(
                {"success": False, "message": "Invalid Kenyan M-Pesa number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        accountant = getattr(user, "accountant_profile", None)
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
                account_reference=str(student.admission_number),
                transaction_desc=(description[:100] if description else
                    f"School Fees - {student.first_name} {student.last_name}"),
            )
        except Exception as e:
            payment.payment_status = FeePayment.PaymentStatus.FAILED
            payment.result_description = str(e)
            payment.save(update_fields=["payment_status", "result_description"])
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.merchant_request_id = response.get("MerchantRequestID", "")
        payment.checkout_request_id = response.get("CheckoutRequestID", "")
        payment.save(update_fields=["merchant_request_id", "checkout_request_id"])

        return Response(
            {
                "success": True,
                "message": "STK Push sent successfully.",
                "payment_id": payment.id,
                "student_id": student.id,
                "student_name": f"{student.first_name} {student.last_name}",
                "amount": payment.amount,
                "merchant_request_id": payment.merchant_request_id,
                "checkout_request_id": payment.checkout_request_id,
                "customer_message": response.get("CustomerMessage"),
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
        callback = data.get("Body", {}).get("stkCallback", {})
        checkout_request_id = callback.get("CheckoutRequestID")

        if not checkout_request_id:
            return Response({"ResultCode": 0, "ResultDesc": "No CheckoutRequestID."})

        MpesaCallbackLog.objects.get_or_create(
            checkout_request_id=checkout_request_id,
            defaults={"payload": data},
        )

        try:
            payment = FeePayment.objects.get(checkout_request_id=checkout_request_id)
        except FeePayment.DoesNotExist:
            return Response({"ResultCode": 0, "ResultDesc": "Payment not found."})

        if payment.payment_status == FeePayment.PaymentStatus.SUCCESS:
            return Response({"ResultCode": 0, "ResultDesc": "Already processed."})

        result_code = callback.get("ResultCode")
        result_desc = callback.get("ResultDesc")
        payment.result_code = str(result_code)
        payment.result_description = result_desc

        if result_code == 0:
            metadata = {}
            items = callback.get("CallbackMetadata", {}).get("Item", [])
            for item in items:
                name = item.get("Name")
                if name:
                    metadata[name] = item.get("Value")

            payment.mpesa_receipt = metadata.get("MpesaReceiptNumber")
            if metadata.get("PhoneNumber"):
                payment.phone_number = str(metadata.get("PhoneNumber"))
            payment.transaction_date = timezone.now()

            with transaction.atomic():
                student_fee = StudentFee.objects.select_for_update().get(
                    id=payment.student_fee_id
                )
                student_fee.amount_paid += payment.amount
                student_fee.balance = max(
                    student_fee.total_fee - student_fee.amount_paid, 0
                )
                student_fee.save(update_fields=["amount_paid", "balance"])
                payment.payment_status = FeePayment.PaymentStatus.SUCCESS
                payment.save()
        else:
            payment.payment_status = FeePayment.PaymentStatus.FAILED
            payment.save(update_fields=[
                "result_code", "result_description", "payment_status"
            ])

        return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

# =====================================================
# RECEIPT BY NUMBER
# =====================================================
class ReceiptByNumberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, receipt_number):
        try:
            payment = FeePayment.objects.select_related(
                "student_fee",
                "student_fee__student",
                "student_fee__student__parent",
            ).get(receipt_number=receipt_number)
        except FeePayment.DoesNotExist:
            return Response(
                {"detail": "Receipt not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user
        role = getattr(user, "role", None)
        allowed_staff = ["SUPER_ADMIN", "ACCOUNTANT", "ACADEMIC_COORDINATOR"]

        if role == "PARENT":
            parent_profile = getattr(user, "parent_profile", None)
            if (not parent_profile or
                payment.student_fee.student.parent_id != parent_profile.id):
                return Response(
                    {"detail": "Not authorized to view this receipt."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif role not in allowed_staff:
            return Response(
                {"detail": "Not authorized to view this receipt."},
                status=status.HTTP_403_FORBIDDEN,
            )

        student = payment.student_fee.student
        return Response({
            "id": payment.id,
            "receipt_number": payment.receipt_number,
            "student_name": f"{student.first_name} {student.last_name}",
            "admission_number": student.admission_number,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "payment_status": payment.payment_status,
            "payment_date": payment.payment_date,
            "phone_number": payment.phone_number,
            "mpesa_receipt": payment.mpesa_receipt,
            "result_description": payment.result_description,
            "transaction_date": payment.transaction_date,
        }, status=status.HTTP_200_OK)