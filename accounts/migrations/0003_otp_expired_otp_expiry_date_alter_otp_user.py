# Generated by Django 4.1.7 on 2023-03-12 14:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_is_verified"),
    ]

    operations = [
        migrations.AddField(
            model_name="otp",
            name="expired",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="otp",
            name="expiry_date",
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name="otp",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="otp",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]