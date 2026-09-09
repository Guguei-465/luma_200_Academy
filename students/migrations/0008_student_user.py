# Generated manually to link students.Student to accounts.CustomUser

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('students', '0007_alter_student_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='user',
            field=models.OneToOneField(
                blank=True,
                limit_choices_to={'role': 'STUDENT'},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='student_record',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
