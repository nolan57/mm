# Generated by Django 5.1.3 on 2024-12-15 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("conferenceApp", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="address",
            field=models.CharField(blank=True, max_length=500, verbose_name="公司地址"),
        ),
        migrations.AddField(
            model_name="company",
            name="contact_email",
            field=models.EmailField(
                blank=True, max_length=254, verbose_name="联系人邮箱"
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="contact_name",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="联系人姓名"
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="contact_phone",
            field=models.CharField(
                blank=True, max_length=20, verbose_name="联系人电话"
            ),
        ),
    ]
