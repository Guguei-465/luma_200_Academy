from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    ParentProfile,
    TeacherProfile,
    AccountantProfile,
    AcademicCoordinatorProfile,
    StudentProfile,
)

User = get_user_model()


# ==========================================
# User Serializer
# ==========================================
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "profile_picture",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]


# ==========================================
# Registration Serializer
# ==========================================
class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "password",
            "role",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


# ==========================================
# Parent Profile Serializer
# ==========================================
class ParentProfileSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)

    class Meta:
        model = ParentProfile
        fields = "__all__"


# ==========================================
# Teacher Profile Serializer
# ==========================================
class TeacherProfileSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = "__all__"


# ==========================================
# Accountant Profile Serializer
# ==========================================
class AccountantProfileSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)

    class Meta:
        model = AccountantProfile
        fields = "__all__"


# ==========================================
# Academic Coordinator Serializer
# ==========================================
class AcademicCoordinatorProfileSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)

    class Meta:
        model = AcademicCoordinatorProfile
        fields = "__all__"



# --- Student ---
class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id", "user", "admission_number", "national_id",
            "gender", "date_of_birth", "created_at", "updated_at"
        ]        