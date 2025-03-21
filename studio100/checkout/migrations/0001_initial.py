# Generated by Django 5.1.4 on 2025-01-12 18:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('admin_panel', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='invoices',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('amount', models.BigIntegerField()),
                ('status', models.CharField(max_length=6)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_panel.user_data')),
            ],
        ),
    ]
