from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import (
    ConsultaClienteForm,
    InicioSesionForm,
    ProductoForm,
    RegistroForm,
)
from .models import (
    Compra,
    DetalleCompra,
    OrdenCompra,
    Producto,
    StockProducto,
)


def _formatear_clp(valor):
    return f"${int(valor):,}".replace(',', '.')


def _datos_producto(producto, stock):
    return {
        'id': producto.pk,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'categoria': producto.categoria.nombre,
        'precio_clp': producto.precio_clp,
        'precio_formateado': _formatear_clp(producto.precio_clp),
        'imagen_url': producto.imagen_url,
        'stock': stock,
        'disponible': stock > 0,
    }


def _cargar_productos():
    productos = list(
        Producto.objects.select_related('categoria').order_by('pk')
    )
    stocks = StockProducto.objects.in_bulk(
        [producto.pk for producto in productos],
        field_name='producto_id',
    )
    datos = []
    for producto in productos:
        stock = stocks.get(producto.pk)
        if stock is None:
            stock, _ = StockProducto.objects.get_or_create(
                producto_id=producto.pk,
                defaults={'stock': 0},
            )
        datos.append(_datos_producto(producto, stock.stock))
    return datos


def _total_items(carrito):
    return sum(int(cantidad) for cantidad in carrito.values())


def _productos_por_id():
    return {producto['id']: producto for producto in _cargar_productos()}


def inicio(request):
    productos = _cargar_productos()
    return render(
        request,
        'catalogo/inicio.html',
        {
            'productos_destacados': [
                producto for producto in productos if producto['disponible']
            ][:3],
            'total_productos': len(productos),
            'total_items_carrito': _total_items(
                request.session.get('carrito', {})
            ),
        },
    )


def lista_productos(request):
    productos = _cargar_productos()
    resumen = {
        'total': len(productos),
        'disponibles': sum(producto['disponible'] for producto in productos),
        'sin_stock': sum(not producto['disponible'] for producto in productos),
    }
    return render(
        request,
        'catalogo/lista.html',
        {
            'productos': productos,
            'categorias': sorted({producto['categoria'] for producto in productos}),
            'resumen': resumen,
            'total_items_carrito': _total_items(
                request.session.get('carrito', {})
            ),
        },
    )


def detalle_producto(request, producto_id):
    producto = _productos_por_id().get(producto_id)
    if producto is None:
        raise Http404('El producto no existe')
    return render(request, 'catalogo/detalle.html', {'producto': producto})


@login_required
@require_POST
def comprar_producto(request, producto_id):
    producto = get_object_or_404(Producto.objects.select_related('categoria'), pk=producto_id)
    with transaction.atomic():
        stock, _ = StockProducto.objects.select_for_update().get_or_create(
            producto_id=producto_id,
            defaults={'stock': 0},
        )
        if stock.stock == 0:
            messages.error(request, 'Este producto no tiene stock disponible.')
            return redirect('detalle_producto', producto_id=producto_id)
        stock.stock -= 1
        stock.save(update_fields=('stock', 'actualizado_en'))
        Compra.objects.create(
            usuario=request.user,
            producto_id=producto_id,
            cantidad=1,
        )

    messages.success(
        request,
        f'Compra realizada: {producto.nombre}. Stock restante: {stock.stock}.',
    )
    return redirect('detalle_producto', producto_id=producto_id)


def registro(request):
    if request.user.is_authenticated:
        return redirect('lista_productos')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, 'Tu cuenta fue creada correctamente.')
        return redirect('lista_productos')
    return render(request, 'catalogo/registro.html', {'form': form})


def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('lista_productos')

    form = InicioSesionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if usuario is not None:
            login(request, usuario)
            destino = request.POST.get('next') or request.GET.get('next', '')
            if url_has_allowed_host_and_scheme(
                destino,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(destino)
            return redirect('lista_productos')
        form.add_error(None, 'El usuario o la contraseña no son correctos.')
    return render(request, 'catalogo/iniciar_sesion.html', {'form': form})


@login_required
def cerrar_sesion(request):
    if request.method == 'POST':
        logout(request)
    return redirect('lista_productos')


def es_administrador(usuario):
    return usuario.is_authenticated and usuario.is_staff


@user_passes_test(es_administrador)
def administrar_stock(request):
    if request.method == 'POST':
        try:
            producto_id = int(request.POST['producto_id'])
            cantidad = int(request.POST['cantidad'])
            operacion = request.POST['operacion']
            if cantidad <= 0 or operacion not in {'sumar', 'restar'}:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            messages.error(request, 'Indica una cantidad positiva y una operación válida.')
        else:
            try:
                with transaction.atomic():
                    stock = StockProducto.objects.select_for_update().get(
                        producto_id=producto_id
                    )
                    if operacion == 'sumar':
                        stock.stock += cantidad
                    else:
                        stock.stock = max(0, stock.stock - cantidad)
                    stock.save(update_fields=('stock', 'actualizado_en'))
            except StockProducto.DoesNotExist:
                messages.error(request, 'No se encontró el stock de ese producto.')
            else:
                messages.success(
                    request,
                    f'Stock actualizado correctamente: {stock.stock} unidades.',
                )
        return redirect('administrar_stock')

    return render(
        request,
        'catalogo/administrar_stock.html',
        {'productos': _cargar_productos()},
    )


def agregar_al_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('lista_productos')
    producto = _productos_por_id().get(producto_id)
    if producto is None:
        raise Http404('El producto no existe')
    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        cantidad = 0
    carrito = request.session.get('carrito', {})
    cantidad_actual = int(carrito.get(str(producto_id), 0))
    if cantidad < 1:
        messages.error(request, 'Indica una cantidad válida.')
    elif cantidad_actual + cantidad > producto['stock']:
        messages.error(request, 'La cantidad solicitada supera el stock disponible.')
    else:
        carrito[str(producto_id)] = cantidad_actual + cantidad
        request.session['carrito'] = carrito
        messages.success(request, f'{producto["nombre"]} se añadió al carrito.')
    return redirect('lista_productos')


def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    productos = _productos_por_id()
    items_carrito = []
    subtotal_neto = Decimal('0')
    carrito_valido = {}
    for prod_id, cantidad in carrito.items():
        try:
            producto_id = int(prod_id)
            cantidad = int(cantidad)
        except (TypeError, ValueError):
            continue
        producto = productos.get(producto_id)
        if producto is None or cantidad < 1:
            continue
        carrito_valido[str(producto_id)] = cantidad
        subtotal = Decimal(producto['precio_clp']) * cantidad
        subtotal_neto += subtotal
        items_carrito.append(
            {
                'producto': producto,
                'cantidad': cantidad,
                'subtotal_formateado': _formatear_clp(subtotal),
            }
        )
    if carrito_valido != carrito:
        request.session['carrito'] = carrito_valido
        messages.warning(request, 'Se quitaron del carrito productos que ya no están disponibles.')

    total_iva = (subtotal_neto * Decimal('0.19')).quantize(
        Decimal('1'), rounding=ROUND_HALF_UP
    )
    return render(
        request,
        'catalogo/carrito.html',
        {
            'items_carrito': items_carrito,
            'subtotal_neto': subtotal_neto,
            'subtotal_neto_formateado': _formatear_clp(subtotal_neto),
            'total_iva': total_iva,
            'total_iva_formateado': _formatear_clp(total_iva),
            'total_general': subtotal_neto + total_iva,
            'total_general_formateado': _formatear_clp(subtotal_neto + total_iva),
            'total_items_carrito': _total_items(carrito_valido),
        },
    )


@require_POST
def actualizar_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    clave = str(producto_id)
    try:
        cantidad = int(request.POST.get('cantidad', 0))
    except (TypeError, ValueError):
        cantidad = 0
    producto = _productos_por_id().get(producto_id)
    if cantidad <= 0:
        carrito.pop(clave, None)
    elif producto is None or cantidad > producto['stock']:
        messages.error(request, 'La cantidad solicitada supera el stock disponible.')
    else:
        carrito[clave] = cantidad
    request.session['carrito'] = carrito
    return redirect('carrito')


@require_POST
def eliminar_del_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    carrito.pop(str(producto_id), None)
    request.session['carrito'] = carrito
    return redirect('carrito')


@require_POST
def vaciar_carrito(request):
    request.session['carrito'] = {}
    return redirect('carrito')


@login_required
@require_POST
def compra(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.error(request, 'El carrito está vacío.')
        return redirect('carrito')
    try:
        cantidades = {int(prod_id): int(cantidad) for prod_id, cantidad in carrito.items()}
    except (TypeError, ValueError):
        messages.error(request, 'El carrito contiene cantidades inválidas.')
        return redirect('carrito')
    if any(cantidad < 1 for cantidad in cantidades.values()):
        messages.error(request, 'El carrito contiene cantidades inválidas.')
        return redirect('carrito')

    with transaction.atomic():
        stocks = {
            stock.producto_id: stock
            for stock in StockProducto.objects.select_for_update().filter(
                producto_id__in=cantidades
            )
        }
        productos = {
            producto.pk: producto
            for producto in Producto.objects.select_for_update().filter(
                pk__in=cantidades
            )
        }
        if len(stocks) != len(cantidades) or len(productos) != len(cantidades):
            messages.error(request, 'Un producto del carrito ya no está disponible.')
            return redirect('carrito')
        if any(stocks[product_id].stock < cantidad for product_id, cantidad in cantidades.items()):
            messages.error(request, 'No hay stock suficiente para completar la compra.')
            return redirect('carrito')

        subtotal_neto = sum(
            (
                Decimal(productos[product_id].precio_clp) * cantidad
                for product_id, cantidad in cantidades.items()
            ),
            Decimal('0'),
        )
        total_iva = (subtotal_neto * Decimal('0.19')).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP
        )
        orden = OrdenCompra.objects.create(
            usuario=request.user,
            total=subtotal_neto + total_iva,
        )
        for product_id, cantidad in cantidades.items():
            producto = productos[product_id]
            stock = stocks[product_id]
            stock.stock -= cantidad
            stock.save(update_fields=('stock', 'actualizado_en'))
            DetalleCompra.objects.create(
                orden=orden,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio_clp,
            )
            Compra.objects.create(
                usuario=request.user,
                producto_id=product_id,
                cantidad=cantidad,
            )

    request.session['carrito'] = {}
    messages.success(
        request,
        f'Compra registrada. Total pagado: {_formatear_clp(orden.total)}.',
    )
    return redirect('lista_productos')


@method_decorator(user_passes_test(es_administrador), name='dispatch')
class ProductoCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'catalogo/producto_form.html'
    success_url = reverse_lazy('lista_productos')


@method_decorator(user_passes_test(es_administrador), name='dispatch')
class ProductoUpdateView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'catalogo/producto_form.html'
    success_url = reverse_lazy('lista_productos')


@method_decorator(user_passes_test(es_administrador), name='dispatch')
class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = 'catalogo/producto_confirm_delete.html'
    success_url = reverse_lazy('lista_productos')

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            StockProducto.objects.filter(producto_id=self.object.pk).delete()
        return response


@user_passes_test(es_administrador)
def reporte_agrupado(request):
    resumenes = defaultdict(lambda: {'cantidad_productos': 0, 'total_stock': 0, 'precio_total': 0})
    stocks = {
        stock.producto_id: stock.stock
        for stock in StockProducto.objects.all()
    }
    for producto in Producto.objects.values('pk', 'categoria__nombre', 'precio_clp'):
        fila = resumenes[producto['categoria__nombre']]
        fila['cantidad_productos'] += 1
        fila['total_stock'] += stocks.get(producto['pk'], 0)
        fila['precio_total'] += producto['precio_clp']

    reportes = [
        {
            'categoria': categoria,
            'cantidad_productos': valores['cantidad_productos'],
            'total_stock': valores['total_stock'],
            'precio_promedio': Decimal(valores['precio_total']) / valores['cantidad_productos'],
        }
        for categoria, valores in sorted(resumenes.items())
    ]
    return render(request, 'catalogo/reporte_agrupado.html', {'reportes': reportes})


@user_passes_test(es_administrador)
def reporte_stock_critico(request):
    productos_criticos = [
        producto
        for producto in _cargar_productos()
        if producto['stock'] <= 5
    ]
    productos_criticos.sort(key=lambda producto: (producto['stock'], producto['nombre']))
    return render(
        request,
        'catalogo/reporte_stock.html',
        {'productos': productos_criticos},
    )


def contacto_cliente(request):
    visitas = request.session.get('visitas_contacto', 0) + 1
    request.session['visitas_contacto'] = visitas
    form = ConsultaClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        consulta = form.save(commit=False)
        if request.user.is_authenticated:
            consulta.usuario = request.user
        consulta.save()
        messages.success(request, 'Tu consulta fue enviada correctamente.')
        return redirect('lista_productos')
    return render(
        request,
        'catalogo/contacto.html',
        {'form': form, 'visitas_contacto': visitas},
    )
