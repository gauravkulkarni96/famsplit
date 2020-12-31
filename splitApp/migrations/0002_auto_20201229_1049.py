# Generated by Django 3.1.4 on 2020-12-29 10:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('splitApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_on', models.DateTimeField(blank=True, null=True)),
                ('title', models.CharField(blank=True, max_length=500, null=True)),
                ('bill_amount', models.FloatField(default=0)),
                ('added_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bill', to='splitApp.user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_on', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('simplify_payments', models.BooleanField(default=False)),
                ('default_currency', models.CharField(choices=[('INR', 'inr'), ('USD', 'usd')], default='INR', max_length=20)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='group', to='splitApp.user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_on', models.DateTimeField(blank=True, null=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='membership', to='splitApp.group')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='membership', to='splitApp.user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_on', models.DateTimeField(blank=True, null=True)),
                ('amount_paid', models.FloatField(default=0)),
                ('amount_owed', models.FloatField(default=0)),
                ('bill', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='expense', to='splitApp.bill')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='expense', to='splitApp.user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='bill',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bill', to='splitApp.group'),
        ),
    ]
