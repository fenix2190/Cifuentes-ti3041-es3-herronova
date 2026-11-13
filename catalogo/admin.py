from django.contrib import admin

from .models import (
    Categoria,
    Compra,
    ConsultaCliente,
    DetalleCompra,
    OrdenCompra,
    Producto,
    StockProducto,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_clp')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'categoria__nombre')


@admin.register(StockProducto)
class StockProductoAdmin(admin.ModelAdmin):
    list_display = ('producto_id', 'stock', 'actualizado_en')
    search_fields = ('producto_id',)


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'producto_id', 'cantidad', 'creada_en')
    list_filter = ('creada_en',)
    search_fields = ('usuario__username', 'producto_id')


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'total', 'creada_en')
    list_filter = ('creada_en',)
    search_fields = ('usuario__username',)


@admin.register(DetalleCompra)
class DetalleCompraAdmin(admin.ModelAdmin):
    list_display = ('orden', 'producto', 'cantidad', 'precio_unitario')
    search_fields = ('producto__nombre', 'orden__usuario__username')


@admin.register(ConsultaCliente)
class ConsultaClienteAdmin(admin.ModelAdmin):
    list_display = ('asunto', 'nombre', 'correo', 'creada_en', 'respondida')
    list_filter = ('respondida', 'creada_en')
    search_fields = ('nombre', 'correo', 'asunto')
