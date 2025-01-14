# Generated by Django 4.1.7 on 2023-04-04 18:19

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_alter_user_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="id",
            field=models.CharField(
                default=uuid.uuid4,
                editable=False,
                max_length=100,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
    ]
