# Generated by Django 5.1 on 2024-12-15 13:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("conferenceApp", "0003_company_address_company_contact_email_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="company",
            name="contact_email",
        ),
        migrations.RemoveField(
            model_name="company",
            name="contact_name",
        ),
        migrations.RemoveField(
            model_name="company",
            name="contact_phone",
        ),
    ]
