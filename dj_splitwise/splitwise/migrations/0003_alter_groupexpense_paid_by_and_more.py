# Generated by Django 5.1.1 on 2024-09-17 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('splitwise', '0002_group_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupexpense',
            name='paid_by',
            field=models.ManyToManyField(related_name='group_expense', to='splitwise.expensepaidby'),
        ),
        migrations.AlterField(
            model_name='groupexpense',
            name='shared_by',
            field=models.ManyToManyField(related_name='group_expense', to='splitwise.expensesharedby'),
        ),
    ]
