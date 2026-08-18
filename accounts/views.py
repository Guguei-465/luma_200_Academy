from django.contrib.auth import authenticate
from django.db import IntegrityError
from rest_framework.exceptions import NotFound
from rest_framework import permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.db import transaction
from django.shortcuts import get_object_or_404
from accounts.serializers import (
    RegisterSerializer,
    StudentProfileSerializer,
    UserSerializer,
    ParentProfileSerializer,
    TeacherProfileSerializer,
    AccountantProfileSerializer,
    AcademicCoordinatorProfileSerializer,
)
from .models import (
    CustomUser,
    ParentProfile,
    StudentProfile,
    TeacherProfile,
    AccountantProfile,
    AcademicCoordinatorProfile,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

 
# after deleting old model
# NOTE: Student records are managed by the dedicated `students` app.
# The `students.Student` model has no `user` FK, so it is intentionally
# excluded from this role-based profile mapping.
PROFILE_MODELS = {
    CustomUser.Role.PARENT: ParentProfile,
    CustomUser.Role.TEACHER: TeacherProfile,
    CustomUser.Role.ACCOUNTANT: AccountantProfile,
    CustomUser.Role.ACADEMIC_COORDINATOR: AcademicCoordinatorProfile,
}
# Reverse lookup for deleting old profiles
PROFILE_MODELS_BY_ROLE = PROFILE_MODELS


@api_view(["POST"])
@permission_classes([AllowAny])
def Login(request):

    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {"error": "This account has been deactivated."},
            status=status.HTTP_403_FORBIDDEN,
        )

    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "message": "Login successful",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        },
        status=status.HTTP_200_OK,
    )


# Login test
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def test(request):
    return Response(
        {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "role": request.user.role,
        },
        status=status.HTTP_200_OK,
    )

# logout
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def Logout(request):

    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"error": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response(
            {"message": "Logout successful."},
            status=status.HTTP_200_OK,
        )

    except TokenError:
        return Response(
            {"error": "Invalid or expired refresh token."},
            status=status.HTTP_400_BAD_REQUEST,
        )


# Registration
@api_view(["POST"])
@transaction.atomic
@permission_classes([IsAuthenticated])
def Register(request):

    # Only Super Admin can create accounts
    if request.user.role != CustomUser.Role.SUPER_ADMIN:
        return Response(
            {"error": "Only the Super Admin can create user accounts."},
            status=status.HTTP_403_FORBIDDEN,
        )

    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")
    role = request.data.get("role")
    phone_number = request.data.get("phone_number")

    # Required fields
    if not username or not email or not password or not role:
        return Response(
            {"error": "Username, email, password and role are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check username
    if CustomUser.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check email
    if CustomUser.objects.filter(email=email).exists():
        return Response(
            {"error": "Email already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.save()

            if user.role == CustomUser.Role.TEACHER:
                TeacherProfile.objects.create(
                    user=user,
                    employee_number=request.data.get("employee_number"),
                    national_id=request.data.get("national_id"),
                    gender=request.data.get("gender"),
                    date_of_birth=request.data.get("date_of_birth"),
                    qualification=request.data.get("qualification"),
                    employment_date=request.data.get("employment_date"),
                )

            elif user.role == CustomUser.Role.PARENT:
                ParentProfile.objects.create(
                    user=user,
                    occupation=request.data.get("occupation", ""),
                    address=request.data.get("address", ""),
                )

            elif user.role == CustomUser.Role.ACCOUNTANT:
                AccountantProfile.objects.create(
                    user=user,
                    employee_number=request.data.get("employee_number"),
                )

            elif user.role == CustomUser.Role.ACADEMIC_COORDINATOR:
                AcademicCoordinatorProfile.objects.create(
                    user=user,
                    employee_number=request.data.get("employee_number"),
                )

            return Response(
                {
                    "message": "User account created successfully.",
                    "user": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    except IntegrityError as e:
        return Response(
            {
                "error": str(e)
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


# List all users
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def UserList(request):

    if request.user.role != CustomUser.Role.SUPER_ADMIN:
        return Response(
            {"error": "Only the Super Admin can view all users."},
            status=status.HTTP_403_FORBIDDEN,
        )

    users = CustomUser.objects.order_by("id")

    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


# User details
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def UserDetail(request, id):

    if request.user.role != CustomUser.Role.SUPER_ADMIN:
        return Response(
            {"error": "Only the Super Admin can view user details."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        user = get_object_or_404(CustomUser, id=id)

    except CustomUser.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = UserSerializer(user)

    return Response(serializer.data)



# updating users
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def UpdateUser(request, id):
    # Only Super Admin can update users
    if request.user.role != CustomUser.Role.SUPER_ADMIN:
        return Response(
            {"error": "Only the Super Admin can update user accounts."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        user = CustomUser.objects.get(id=id)
    except CustomUser.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    username = request.data.get("username", user.username)
    first_name = request.data.get("first_name", user.first_name)
    last_name = request.data.get("last_name", user.last_name)
    email = request.data.get("email", user.email)
    phone_number = request.data.get("phone_number", user.phone_number)
    role = request.data.get("role", user.role)
    is_active = request.data.get("is_active", user.is_active)

    # Check username uniqueness
    if CustomUser.objects.exclude(id=user.id).filter(username=username).exists():
        return Response(
            {"error": "Username already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check email uniqueness
    if CustomUser.objects.exclude(id=user.id).filter(email=email).exists():
        return Response(
            {"error": "Email already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_role = user.role

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.phone_number = phone_number
    user.role = role
    user.is_active = is_active
    user.save()

<<<<<<< HEAD
    # If the role changed, remove the old profile and create the new one.
    #
    # NOTE: TeacherProfile / AccountantProfile / AcademicCoordinatorProfile
    # all have required fields (employee_number, national_id, gender,
    # date_of_birth, etc.) with no defaults, so a bare
    # get_or_create(user=user) will raise IntegrityError for those roles.
    # We no longer let that crash the request (500) — instead we tell the
    # caller the new profile still needs its required details filled in.
    profile_warning = None

=======
    # If the role changed, remove the old profile and create the new one
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    if old_role != role:
        old_profile_model = PROFILE_MODELS_BY_ROLE.get(old_role)

        if old_profile_model:
            old_profile_model.objects.filter(user=user).delete()

        new_profile_model = PROFILE_MODELS_BY_ROLE.get(role)

        if new_profile_model:
<<<<<<< HEAD
            try:
                new_profile_model.objects.get_or_create(user=user)
            except IntegrityError:
                profile_warning = (
                    f"User role changed to {role}, but the matching "
                    f"profile could not be auto-created because required "
                    f"fields are missing. Please complete the "
                    f"{new_profile_model.__name__} details for this user."
                )

    response_data = {
        "message": "User updated successfully.",
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "role": user.role,
            "is_active": user.is_active,
        },
    }

    if profile_warning:
        response_data["profile_warning"] = profile_warning

    return Response(
        response_data,
=======
            new_profile_model.objects.get_or_create(user=user)

    return Response(
        {
            "message": "User updated successfully.",
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "is_active": user.is_active,
            },
        },
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
        status=status.HTTP_200_OK,
    )


# deletin/deativate user
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def DeleteUser(request, id):
    # Only Super Admin can deactivate users
    if request.user.role != CustomUser.Role.SUPER_ADMIN:
        return Response(
            {"error": "Only the Super Admin can deactivate user accounts."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        user = get_object_or_404(CustomUser, id=id)

    except CustomUser.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Prevent deleting yourself
    if user.id == request.user.id:
        return Response(
            {"error": "You cannot deactivate your own account."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.is_active = False
    user.save()

    return Response(
        {
            "message": "User account has been deactivated successfully."
        },
        status=status.HTTP_200_OK,
    )

# restoring deactivated user
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def RestoreUser(request, id):
    #  only admin can do that
    if request.user.role != CustomUser.Role.SUPER_ADMIN:
        return Response(
            {"error": "Only the Super Admin can restore user accounts."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        user = get_object_or_404(CustomUser, id=id)

    except CustomUser.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    user.is_active = True
    user.save()

    return Response(
        {
            "message": "User account restored successfully."
        },
        status=status.HTTP_200_OK,
    )
 
# changing passord
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ChangePassword(request):
    # anyone can chang his/her password
    user = request.user

    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    # Required fields
    if not old_password or not new_password or not confirm_password:
        return Response(
            {
                "error": "Old password, new password and confirm password are required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check old password
    if not user.check_password(old_password):
        return Response(
            {"error": "Old password is incorrect."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check new password confirmation
    if new_password != confirm_password:
        return Response(
            {"error": "New passwords do not match."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Prevent reusing the same password
    if user.check_password(new_password):
        return Response(
            {"error": "New password must be different from the old password."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
       validate_password(new_password, user)
    except ValidationError as e:
      return Response(
        {"error": e.messages},
        status=status.HTTP_400_BAD_REQUEST,
    )

    # Save the new password
    user.set_password(new_password)
    user.save()

    return Response(
        {"message": "Password changed successfully."},
        status=status.HTTP_200_OK,
    )

# reset passwword
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ResetPassword(request, id):
    # Only Super Admin can reset passwords
    if request.user.role != CustomUser.Role.SUPER_ADMIN:
        return Response(
            {"error": "Only the Super Admin can reset user passwords."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        user = get_object_or_404(CustomUser, id=id)
    except CustomUser.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")

    # Required fields
    if not new_password or not confirm_password:
        return Response(
            {"error": "New password and confirm password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Passwords must match
    if new_password != confirm_password:
        return Response(
            {"error": "Passwords do not match."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Don't reuse the current password
    if user.check_password(new_password):
        return Response(
            {"error": "The new password cannot be the same as the current password."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate password
    try:
        validate_password(new_password, user)
    except ValidationError as e:
        return Response(
            {"error": e.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Save password
    user.set_password(new_password)
    user.save()

    return Response(
        {
            "message": f"Password for '{user.username}' has been reset successfully."
        },
        status=status.HTTP_200_OK,
    )


class AcademicCoordinatorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AcademicCoordinatorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        instance = AcademicCoordinatorProfile.objects.filter(
            user=self.request.user
        ).first()
        if instance is None:
            raise NotFound("Academic coordinator profile not found.")
        return instance


class TeacherProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        instance = TeacherProfile.objects.filter(
            user=self.request.user
        ).first()
        if instance is None:
            raise NotFound("Teacher profile not found.")
        return instance


class AccountantProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AccountantProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        instance = AccountantProfile.objects.filter(
            user=self.request.user
        ).first()
        if instance is None:
            raise NotFound("Accountant profile not found.")
        return instance


class ParentProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ParentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        instance = ParentProfile.objects.filter(
            user=self.request.user
        ).first()
        if instance is None:
            raise NotFound("Parent profile not found.")
        return instance


class StudentProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return StudentProfile.objects.get(user=self.request.user)
        except StudentProfile.DoesNotExist:
            raise NotFound("Student profile not found.")


# ==========================================
# LIST ALL PARENTS
# ==========================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ParentList(request):

<<<<<<< HEAD
    # Only staff roles that legitimately need the full parent/child
    # roster may see it. Without this check, ANY authenticated user
    # (including a Parent or Teacher) could list every family's data,
    # which breaks the parent-isolation principle even though this
    # isn't itself a "parent-scoped" endpoint.
    allowed_roles = [
        CustomUser.Role.SUPER_ADMIN,
        CustomUser.Role.ACADEMIC_COORDINATOR,
        CustomUser.Role.ACCOUNTANT,
    ]

    if request.user.role not in allowed_roles:
        return Response(
            {"error": "You do not have permission to view the parent list."},
            status=status.HTTP_403_FORBIDDEN,
        )

=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    parents = (
        ParentProfile.objects
        .select_related("user")
        .prefetch_related("children")
        .order_by("user__first_name", "user__last_name")
    )

    serializer = ParentProfileSerializer(
        parents,
        many=True
    )

    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )

# ============================================================
# LIST ALL TEACHER PROFILES
# ============================================================
#
# This endpoint is different from TeacherProfileView.
#
# TeacherProfileView:
#     /api/accounts/teacher-profile/
#
#     Returns ONLY the logged-in teacher's own profile.
#
# TeacherProfilesListView:
#     /api/accounts/teacher-profiles/
#
#     Returns ALL registered teacher profiles.
#
# Used by:
#     - Super Admin
#     - Academic Coordinator
#
# ============================================================

class TeacherProfilesListView(generics.ListAPIView):

    serializer_class = TeacherProfileSerializer

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self):

        # ----------------------------------------------------
        # Only Super Admin and Academic Coordinator can
        # access the complete teacher list.
        # ----------------------------------------------------

        allowed_roles = [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
        ]

        if self.request.user.role not in allowed_roles:
            return TeacherProfile.objects.none()

        # ----------------------------------------------------
        # Return ALL teacher profiles.
        #
        # select_related("user") makes sure user information
        # such as first_name, last_name, email, username etc.
        # can be serialized efficiently.
        # ----------------------------------------------------

        return (
            TeacherProfile.objects
            .select_related("user")
            .order_by(
                "user__first_name",
                "user__last_name",
                "id",
            )
        )