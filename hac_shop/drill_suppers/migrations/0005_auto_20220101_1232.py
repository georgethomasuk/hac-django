# Generated by Django 3.2.9 on 2022-01-01 12:32

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('drill_suppers', '0004_transactionrecord_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='drillnight',
            name='cut_off_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='StripeCheckoutSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_id', models.CharField(blank=True, max_length=256, null=True)),
                ('checkout_url', models.URLField(blank=True, null=True)),
                ('transaction_record', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='drill_suppers.transactionrecord')),
            ],
        ),
    ]
