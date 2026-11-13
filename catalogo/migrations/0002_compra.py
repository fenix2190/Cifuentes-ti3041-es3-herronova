from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalogo', '0001_stockproducto'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Compra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('producto_id', models.PositiveIntegerField()),
                ('cantidad', models.PositiveIntegerField(default=1)),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-creada_en',)},
        ),
    ]
