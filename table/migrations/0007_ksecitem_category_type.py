# Generated by Django 5.2 on 2025-05-01 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('table', '0006_ksecitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='ksecitem',
            name='category_type',
            field=models.CharField(choices=[('GE', 'General Education'), ('CE', 'Core Education')], default='GE', max_length=2),
        ),
    ]
