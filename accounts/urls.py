from django.urls import path
from .views import(
     ChangePassword,
    DeleteUser, 
    Login, Logout, Register,
     ResetPassword, RestoreUser, 
    UpdateUser, UserDetail, test, UserList
)
from accounts import views

urlpatterns = [

    # Authentication
    path("login/", Login, name="login"),
    path("logout/", Logout, name="logout"),
    path("test/", test, name="test"),

    # Registration
    path("register/", Register, name="register"),

    # User Management
    path("users/", UserList, name="user-list"),
    path("users/<int:id>/", UserDetail, name="user-detail"),
    path("users/<int:id>/update/", UpdateUser, name="update-user"),
    path("users/<int:id>/delete/", DeleteUser, name="delete-user"),
    path("users/<int:id>/restore/", RestoreUser, name="restore-user"),

    # Password Management
    path("change-password/", ChangePassword, name="change-password"),
    path(
        "reset-password/<int:id>/",
        ResetPassword,
        name="reset-password",
    ),
]