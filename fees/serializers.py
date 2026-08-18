from rest_framework import serializers

from .models import (
    FeeStructure,
    StudentFee,
    FeePayment,
    MpesaCallbackLog,
)


# =====================================================
# Fee Structure
# =====================================================
class FeeStructureSerializer(serializers.ModelSerializer):

    total_fee = serializers.ReadOnlyField()

    class Meta:
        model = FeeStructure
        fields = "__all__"


# =====================================================
# Student Fee
# =====================================================
class StudentFeeSerializer(serializers.ModelSerializer):

    student_name = serializers.SerializerMethodField()
    classroom = serializers.SerializerMethodField()
    term = serializers.CharField(
        source="fee_structure.term",
        read_only=True,
    )
    academic_year = serializers.IntegerField(
        source="fee_structure.academic_year",
        read_only=True,
    )

    class Meta:
        model = StudentFee
        fields = [
            "id",
            "student",
            "student_name",
            "classroom",
            "fee_structure",
            "academic_year",
            "term",
            "total_fee",
            "amount_paid",
            "balance",
        ]

        read_only_fields = [
            "amount_paid",
            "balance",
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_classroom(self, obj):
        return str(obj.fee_structure.classroom)


# =====================================================
# Fee Payment
# =====================================================
class FeePaymentSerializer(serializers.ModelSerializer):

    student_name = serializers.SerializerMethodField()

<<<<<<< HEAD
    # The React payment form (RecordPayment.jsx) posts this field name,
    # but the model's matching field is called `external_reference`.
    # Without this explicit mapping, DRF silently drops the incoming
    # `transaction_ref` value and it never gets saved anywhere.
    transaction_ref = serializers.CharField(
        source="external_reference",
        required=False,
        allow_blank=True,
    )

=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    class Meta:
        model = FeePayment
        fields = "__all__"

        read_only_fields = [
            "payment_status",
            "mpesa_receipt",
            "merchant_request_id",
            "checkout_request_id",
            "transaction_date",
            "result_code",
            "result_description",
            "is_reconciled",
            "created_at",
            "updated_at",
<<<<<<< HEAD
            # received_by must never come from the client — the view
            # sets it from the logged-in accountant's own profile.
            "received_by",
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
        ]

    def get_student_name(self, obj):
        return (
            f"{obj.student_fee.student.first_name} "
            f"{obj.student_fee.student.last_name}"
        )

<<<<<<< HEAD
    def validate(self, data):
        """
        SPEC RULE (fees, T5): amount paid can never exceed the
        student's total fee / remaining balance. The STK-push flow
        already enforces this (StkPushSerializer) — this is the
        manual/cash/bank recording path used directly against
        FeePaymentViewSet, which previously had NO such check.
        """

        student_fee = data.get("student_fee") or getattr(
            self.instance, "student_fee", None
        )

        amount = data.get("amount")
        if amount is None and self.instance is not None:
            amount = self.instance.amount

        if amount is not None and amount <= 0:
            raise serializers.ValidationError(
                {"amount": "Amount must be greater than zero."}
            )

        if student_fee is not None and amount is not None:

            # The balance already reflects this payment's OLD amount
            # (if we're editing an existing successful payment), so
            # add that back before comparing, otherwise every edit
            # of an existing payment would falsely look like an
            # overpayment.
            available_balance = student_fee.balance

            if (
                self.instance is not None
                and self.instance.student_fee_id == student_fee.id
                and self.instance.payment_status
                == FeePayment.PaymentStatus.SUCCESS
            ):
                available_balance += self.instance.amount

            if amount > available_balance:
                raise serializers.ValidationError(
                    {
                        "amount": (
                            "Amount exceeds remaining balance "
                            f"({available_balance})."
                        )
                    }
                )

        return data

=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d

# =====================================================
# M-Pesa Callback Log
# =====================================================
class MpesaCallbackLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = MpesaCallbackLog
        fields = "__all__"


# =====================================================
# STK Push Serializer
# =====================================================

class StkPushSerializer(serializers.Serializer):

    student_fee = serializers.PrimaryKeyRelatedField(
        queryset=StudentFee.objects.all()
    )

    phone_number = serializers.CharField(
        max_length=15
    )

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    def validate_phone_number(self, value):
        """
        Convert Kenyan numbers to 2547XXXXXXXX format.
        """

        value = value.strip()

        if value.startswith("+254"):
            value = value.replace("+", "")

        elif value.startswith("07"):
            value = "254" + value[1:]

        elif value.startswith("7"):
            value = "254" + value

        if not value.startswith("254"):
            raise serializers.ValidationError(
                "Phone number must start with 254."
            )

        if len(value) != 12 or not value.isdigit():
            raise serializers.ValidationError(
                "Invalid phone number."
            )

        return value

    def validate(self, data):

        student_fee = data["student_fee"]
        amount = data["amount"]

        if amount <= 0:
            raise serializers.ValidationError(
                {
                    "amount": "Amount must be greater than zero."
                }
            )

        if amount > student_fee.balance:
            raise serializers.ValidationError(
                {
                    "amount":
                    f"Amount exceeds remaining balance ({student_fee.balance})."
                }
            )

        return data