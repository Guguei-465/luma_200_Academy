from django.contrib import admin
from .models import Student, ClassRoom



# Register your models here.
@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'stream')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_no', 'first_name', 'last_name', 'gender', 'classroom')
    search_fields = ('admission_no', 'first_name', 'last_name')
    list_filter = ('gender', 'classroom')