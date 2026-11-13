from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='StockProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('producto_id', models.PositiveIntegerField(unique=True)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ('producto_id',)},
        ),
    ]
