import json
from pathlib import Path

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def cargar_catalogo(apps, schema_editor):
    Categoria = apps.get_model('catalogo', 'Categoria')
    Producto = apps.get_model('catalogo', 'Producto')
    StockProducto = apps.get_model('catalogo', 'StockProducto')
    archivo_productos = Path(settings.BASE_DIR) / 'productos.json'
    with archivo_productos.open(encoding='utf-8') as archivo:
        productos = json.load(archivo)

    productos_sin_stock = {8, 17, 26, 34, 40}
    for item in productos:
        categoria, _ = Categoria.objects.get_or_create(
            nombre=item['categoria']
        )
        Producto.objects.update_or_create(
            pk=item['id'],
            defaults={
                'nombre': item['nombre'],
                'descripcion': item['descripcion'],
                'categoria': categoria,
                'precio_clp': item['precio_clp'],
                'imagen_url': item.get('imagen_url', ''),
            },
        )
        StockProducto.objects.get_or_create(
            producto_id=item['id'],
            defaults={
                'stock': 0 if item['id'] in productos_sin_stock else 12,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0002_compra'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'ordering': ('nombre',),
            },
        ),
        migrations.CreateModel(
            name='OrdenCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('total', models.DecimalField(decimal_places=0, max_digits=10)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ordenes_compra', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-creada_en',),
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField()),
                ('precio_clp', models.PositiveIntegerField()),
                ('imagen_url', models.URLField(blank=True, max_length=1000)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='productos', to='catalogo.categoria')),
            ],
            options={
                'ordering': ('nombre',),
            },
        ),
        migrations.CreateModel(
            name='ConsultaCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=70)),
                ('correo', models.EmailField(max_length=254)),
                ('telefono', models.CharField(blank=True, max_length=20)),
                ('asunto', models.CharField(max_length=150)),
                ('mensaje', models.TextField()),
                ('creada_en', models.DateTimeField(auto_now_add=True)),
                ('respondida', models.BooleanField(default=False)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consultas_cliente', to=settings.AUTH_USER_MODEL)),
                ('producto_interes', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consultas', to='catalogo.producto')),
            ],
            options={
                'ordering': ('-creada_en',),
            },
        ),
        migrations.CreateModel(
            name='DetalleCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField()),
                ('precio_unitario', models.PositiveIntegerField()),
                ('orden', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='catalogo.ordencompra')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='detalles_compra', to='catalogo.producto')),
            ],
            options={
                'constraints': [models.CheckConstraint(condition=models.Q(('cantidad__gt', 0)), name='catalogo_detalle_cantidad_positiva'), models.CheckConstraint(condition=models.Q(('precio_unitario__gte', 0)), name='catalogo_detalle_precio_no_negativo')],
            },
        ),
        migrations.RunPython(cargar_catalogo, migrations.RunPython.noop),
    ]
