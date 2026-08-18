from rest_framework import serializers

from accounts.models import CustomUser, ParentProfile
from students.models import Student, StudentTransfer


# =====================================================
# Student Serializer
# =====================================================

class StudentSerializer(serializers.ModelSerializer):

    classroom_name = serializers.SerializerMethodField()
    class_teacher = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    # =================================================
    # Parent phone number
    #
    # Used when creating a student.
    # It is NOT stored directly on Student.
    # =================================================

    phone_number = serializers.CharField(
        write_only=True,
        required=False,
    )

    # =================================================
    # Optional login account link
    #
    # Lets the admin/coordinator connect this academic
    # record to an EXISTING login account (role=STUDENT)
    # that doesn't yet have a classroom/parent attached.
    # Not required — a roster entry can exist without a
    # login account yet, or vice versa.
    # =================================================

    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(
            role=CustomUser.Role.STUDENT,
            student_record__isnull=True,
        ),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Student

        fields = [
            "id",
            "user",
            "username",
            "admission_number",
            "assessment_number",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",

            "classroom",
            "classroom_name",
            "class_teacher",

            # Parent
            "phone_number",
            "parent_name",

            "status",
            "photo",
            "date_admitted",
            "date_left",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "date_admitted",
            "created_at",
            "updated_at",
            "classroom_name",
            "class_teacher",
            "parent_name",
            "username",
        ]

    # =================================================
    # Linked login username (if any)
    # =================================================

    def get_username(self, obj):

        if obj.user:
            return obj.user.username

        return None

    def validate_user(self, value):

        if value is None:
            return value

        # Re-check freshness on update: the queryset above already
        # excludes users with a student_record, but on PATCH/PUT the
        # instance being edited is allowed to keep its own user.
        already_linked = Student.objects.filter(
            user=value
        ).exclude(
            pk=self.instance.pk if self.instance else None
        )

        if already_linked.exists():
            raise serializers.ValidationError(
                "This login account is already linked to another "
                "student record."
            )

        return value

    # =================================================
    # Classroom name
    # =================================================

    def get_classroom_name(self, obj):

        if obj.classroom:
            return str(obj.classroom)

        return None

    # =================================================
    # Class teacher
    # =================================================

    def get_class_teacher(self, obj):

        if (
            obj.classroom
            and obj.classroom.class_teacher
        ):
            return obj.classroom.class_teacher.user.get_full_name()

        return None

    # =================================================
    # Parent name
    # =================================================

    def get_parent_name(self, obj):

        if obj.parent:
            return obj.parent.user.get_full_name()

        return None

    # =================================================
    # Validate parent phone number
    # =================================================

    def validate_phone_number(self, value):

        try:

            ParentProfile.objects.get(
                user__phone_number=value
            )

        except ParentProfile.DoesNotExist:

            raise serializers.ValidationError(
                "No parent account was found with this phone number."
            )

        return value

    # =================================================
    # Create student
    #
    # Parent phone
    #      ↓
    # ParentProfile
    #      ↓
    # Student.parent
    # =================================================

    def _resolve_parent(self, phone_number):

        try:

            return ParentProfile.objects.get(
                user__phone_number=phone_number
            )

        except ParentProfile.DoesNotExist:

            raise serializers.ValidationError({
                "phone_number":
                    "No parent account was found with this phone number."
            })

    def create(self, validated_data):

        phone_number = validated_data.pop(
            "phone_number", None
        )

        if not phone_number:
            raise serializers.ValidationError({
                "phone_number":
                    "Parent/guardian phone number is required to link "
                    "a new student to their parent account."
            })

        parent = self._resolve_parent(phone_number)

        student = Student.objects.create(
            parent=parent,
            **validated_data
        )

        return student

    def update(self, instance, validated_data):

        # phone_number is optional on update — only re-link the
        # parent if a new number was actually supplied.
        phone_number = validated_data.pop("phone_number", None)

        if phone_number:
            instance.parent = self._resolve_parent(phone_number)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance


# =====================================================
# Student List Serializer
# =====================================================

class StudentListSerializer(serializers.ModelSerializer):

    classroom_name = serializers.SerializerMethodField()
    class_teacher = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    class Meta:
        model = Student

        fields = [
            "id",
            "user",
            "username",
            "admission_number",
            "assessment_number",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",

            "classroom",
            "classroom_name",
            "class_teacher",

            "parent_name",

            "status",
            "photo",
            "date_admitted",
            "date_left",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_username(self, obj):

        if obj.user:
            return obj.user.username

        return None

    # =================================================
    # Classroom name
    # =================================================

    def get_classroom_name(self, obj):

        if obj.classroom:
            return str(obj.classroom)

        return None

    # =================================================
    # Class teacher
    # =================================================

    def get_class_teacher(self, obj):

        if (
            obj.classroom
            and obj.classroom.class_teacher
        ):
            return obj.classroom.class_teacher.user.get_full_name()

        return None

    # =================================================
    # Parent name
    # =================================================

    def get_parent_name(self, obj):

        if obj.parent:
            return obj.parent.user.get_full_name()

        return None


# =====================================================
# Student Transfer Serializer
# =====================================================

class StudentTransferSerializer(
    serializers.ModelSerializer
):

    student_name = serializers.CharField(
        source="student.__str__",
        read_only=True,
    )

    from_classroom_name = serializers.SerializerMethodField()
    to_classroom_name = serializers.SerializerMethodField()
    transferred_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentTransfer

        fields = [
            "id",
            "student",
            "student_name",

            "from_classroom",
            "from_classroom_name",

            "to_classroom",
            "to_classroom_name",

            "transferred_by",
            "transferred_by_name",

            "reason",
            "transfer_date",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "student_name",
            "from_classroom_name",
            "to_classroom_name",
            "transferred_by",
            "transferred_by_name",
            "transfer_date",
            "created_at",
            "updated_at",
        ]

    # =================================================
    # From classroom name
    # =================================================

    def get_from_classroom_name(self, obj):

        return str(obj.from_classroom)

    # =================================================
    # To classroom name
    # =================================================

    def get_to_classroom_name(self, obj):

        return str(obj.to_classroom)

    # =================================================
    # Person who performed transfer
    # =================================================

    def get_transferred_by_name(self, obj):

        if obj.transferred_by:
            return obj.transferred_by.get_full_name()

        return None

    # =================================================
    # Validate transfer
    # =================================================

    def validate(self, attrs):

        # Prevent transferring to same classroom
        if (
            attrs["from_classroom"]
            == attrs["to_classroom"]
        ):

            raise serializers.ValidationError({
                "to_classroom":
                    "Student cannot be transferred to the same classroom."
            })

        # Make sure student's current classroom
        # matches the selected from classroom
        if (
            attrs["student"].classroom
            != attrs["from_classroom"]
        ):

            raise serializers.ValidationError({
                "from_classroom":
                    "The student's current classroom does not match "
                    "the selected from_classroom."
            })

        return attrs