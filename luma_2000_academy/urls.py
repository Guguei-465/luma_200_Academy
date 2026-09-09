"""
URL configuration for luma_2000_academy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

import reports

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("api/accounts/", include("accounts.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/students/", include("students.urls")),
    path("api/classes/", include("classes.urls")),
    path("api/subjects/", include("subjects.urls")),
    path("api/assignments/", include("assignments.urls")),
    path("api/timetable/", include("timetable.urls")),
    path("api/attendance/", include("attendance.urls"),),   
    path("api/exams/", include("exams.urls")),
    path("api/results/", include("results.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/fees/", include("fees.urls")),
    path("api/anouncements/",include("anouncements.urls"),),
    path("api/parents/", include("parents.urls")),
    path("api/notifiations/", include("notifiations.urls")),
]
