# Generated by Django 4.1.7 on 2023-03-13 08:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_alter_otp_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="code",
            field=models.CharField(max_length=4, null=True),
        ),
    ]