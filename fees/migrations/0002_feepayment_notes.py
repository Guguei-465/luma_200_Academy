from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fees", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="feepayment",
            name="notes",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Free-text note entered by the accountant recording the payment.",
            ),
        ),
    ]
