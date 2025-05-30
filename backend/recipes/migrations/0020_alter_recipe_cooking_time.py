# Generated by Django 3.2.3 on 2024-08-15 00:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0019_auto_20240815_0243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1, message='Меньше минуты нелзя'), django.core.validators.MaxValueValidator(32000, message='Блюдо сгорит')], verbose_name='Время приготовления, мин'),
        ),
    ]
