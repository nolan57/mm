# Generated by Django 5.1.3 on 2024-12-16 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("conferenceApp", "0004_remove_company_contact_email_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="registrationform",
            name="logic_rules_json",
            field=models.JSONField(blank=True, null=True, verbose_name="逻辑规则JSON"),
        ),
    ]
