# Generated by Django 3.2.9 on 2022-05-08 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drill_suppers', '0008_auto_20220508_0858'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drillnight',
            name='annotation',
            field=models.CharField(blank=True, help_text='To describe special events like Gun Salutes', max_length=50, null=True),
        ),
    ]
