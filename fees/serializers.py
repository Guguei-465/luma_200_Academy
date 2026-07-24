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
        ]

    def get_student_name(self, obj):
        return (
            f"{obj.student_fee.student.first_name} "
            f"{obj.student_fee.student.last_name}"
        )


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