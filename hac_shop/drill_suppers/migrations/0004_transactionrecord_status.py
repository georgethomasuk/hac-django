# Generated by Django 3.2.9 on 2021-12-30 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drill_suppers', '0003_transactionrecord_drill_night'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactionrecord',
            name='status',
            field=models.CharField(choices=[('awaiting_checkout', 'Awaiting Checkout'), ('paid', 'Paid'), ('refunded', 'Refunded')], default='awaiting_checkout', max_length=31),
        ),
    ]
