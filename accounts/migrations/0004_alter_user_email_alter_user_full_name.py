# Generated by Django 4.1.7 on 2023-03-13 08:08

import accounts.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_otp_expired_otp_expiry_date_alter_otp_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="full_name",
            field=models.CharField(
                max_length=255, validators=[accounts.validators.validate_full_name]
            ),
        ),
    ]