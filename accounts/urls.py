from django.urls import include, path
from .views import (
    ChangePassword, DeleteUser, Login, Logout, Register,
    ResetPassword, RestoreUser, StudentProfileView, UpdateUser, UserDetail, test, UserList,
    AcademicCoordinatorProfileView,
    TeacherProfileView,
    AccountantProfileView,
    ParentProfileView,
)

urlpatterns = [
    # Auth
    path("login/", Login, name="login"),
    path("logout/", Logout, name="logout"),
    path("test/", test, name="test"),
    path('password/reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),

    # Registration
    path("register/", Register, name="register"),

    # User Management
    path("users/", UserList, name="user-list"),
    path("users/<int:id>/", UserDetail, name="user-detail"),
    path("users/<int:id>/update/", UpdateUser, name="update-user"),
    path("users/<int:id>/delete/", DeleteUser, name="delete-user"),
    path("users/<int:id>/restore/", RestoreUser, name="restore-user"),

    # Password
    path("change-password/", ChangePassword, name="change-password"),
    path("reset-password/<int:id>/", ResetPassword, name="reset-password"),

    # ALL PROFILE ENDPOINTS
    path("coordinator-profile/", AcademicCoordinatorProfileView.as_view(), name="coordinator-profile"),
    path("teacher-profile/", TeacherProfileView.as_view(), name="teacher-profile"),
    path("accountant-profile/", AccountantProfileView.as_view(), name="accountant-profile"),
    path("parent-profile/", ParentProfileView.as_view(), name="parent-profile"),
    path("student-profile/", StudentProfileView.as_view(), name="student-profile"),
]