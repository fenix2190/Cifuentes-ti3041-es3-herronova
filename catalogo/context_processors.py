def total_items_carrito(request):
    carrito = request.session.get('carrito', {})
    return {
        'total_items_carrito': sum(
            int(cantidad) for cantidad in carrito.values()
        ),
    }
