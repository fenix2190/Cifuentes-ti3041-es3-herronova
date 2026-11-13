from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ('nombre',)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    precio_clp = models.PositiveIntegerField()
    imagen_url = models.URLField(max_length=1000, blank=True)

    class Meta:
        ordering = ('nombre',)

    def __str__(self):
        return self.nombre


class StockProducto(models.Model):
    producto_id = models.PositiveIntegerField(unique=True)
    stock = models.PositiveIntegerField(default=0)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('producto_id',)

    def __str__(self):
        return f'Producto {self.producto_id}: {self.stock} unidades'


class Compra(models.Model):
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    producto_id = models.PositiveIntegerField()
    cantidad = models.PositiveIntegerField(default=1)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-creada_en',)

    def __str__(self):
        return f'Compra de producto {self.producto_id} por {self.usuario}'


class OrdenCompra(models.Model):
    usuario = models.ForeignKey(
        'auth.User', on_delete=models.PROTECT, related_name='ordenes_compra'
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=0)

    class Meta:
        ordering = ('-creada_en',)

    def __str__(self):
        return f'Orden {self.pk} - {self.usuario}'


class DetalleCompra(models.Model):
    orden = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE, related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='detalles_compra'
    )
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gt=0),
                name='catalogo_detalle_cantidad_positiva',
            ),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0),
                name='catalogo_detalle_precio_no_negativo',
            ),
        ]

    def __str__(self):
        return f'{self.producto} x {self.cantidad}'


class ConsultaCliente(models.Model):
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        related_name='consultas_cliente',
        blank=True,
        null=True,
    )
    nombre = models.CharField(max_length=70)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    asunto = models.CharField(max_length=150)
    producto_interes = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas',
    )
    mensaje = models.TextField()
    creada_en = models.DateTimeField(auto_now_add=True)
    respondida = models.BooleanField(default=False)

    class Meta:
        ordering = ('-creada_en',)

    def __str__(self):
        return self.asunto
