from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Categoria,
    Compra,
    ConsultaCliente,
    DetalleCompra,
    OrdenCompra,
    Producto,
    StockProducto,
)


class ComercioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.producto = Producto.objects.get(pk=1)
        cls.usuario = User.objects.create_user(
            username='comprador',
            password='ClaveSegura123!',
        )

    def test_carrito_y_compra_descuentan_stock_y_guardan_detalle(self):
        self.client.post(
            reverse('agregar_al_carrito', args=[self.producto.pk]),
            {'cantidad': 2},
        )
        self.client.force_login(self.usuario)

        respuesta = self.client.post(reverse('compra'))

        self.assertRedirects(respuesta, reverse('lista_productos'))
        orden = OrdenCompra.objects.get(usuario=self.usuario)
        detalle = DetalleCompra.objects.get(orden=orden)
        stock = StockProducto.objects.get(producto_id=self.producto.pk)
        self.assertEqual(detalle.cantidad, 2)
        self.assertEqual(stock.stock, 10)
        self.assertEqual(Compra.objects.filter(usuario=self.usuario).count(), 1)
        self.assertEqual(self.client.session['carrito'], {})

    def test_catalogo_detalle_y_carrito_se_renderizan(self):
        for ruta in (
            reverse('lista_productos'),
            reverse('detalle_producto', args=[self.producto.pk]),
            reverse('carrito'),
        ):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 200)

    def test_inicio_presenta_herranova_y_enlaza_al_catalogo(self):
        respuesta = self.client.get(reverse('inicio'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Bienvenido a Herranova')
        self.assertContains(respuesta, reverse('lista_productos'))
        self.assertContains(respuesta, 'Nuestra propuesta')

    def test_carrito_no_permite_comprar_mas_que_el_stock(self):
        self.client.post(
            reverse('agregar_al_carrito', args=[self.producto.pk]),
            {'cantidad': 999},
        )

        self.assertNotIn(str(self.producto.pk), self.client.session.get('carrito', {}))

    def test_usuario_no_autenticado_no_puede_confirmar_compra(self):
        respuesta = self.client.post(reverse('compra'))

        self.assertRedirects(
            respuesta,
            f"{reverse('iniciar_sesion')}?next={reverse('compra')}",
        )

    def test_consulta_de_contacto_se_guarda_con_validacion(self):
        respuesta = self.client.post(
            reverse('contacto'),
            {
                'nombre': 'Ana Pérez',
                'correo': 'ana@example.com',
                'telefono': '',
                'asunto': 'Consulta sobre despacho',
                'producto_interes': '',
                'mensaje': 'Necesito información sobre el despacho de este pedido.',
            },
        )

        self.assertRedirects(respuesta, reverse('lista_productos'))
        self.assertEqual(ConsultaCliente.objects.count(), 1)

    def test_consulta_con_mensaje_corto_no_se_guarda(self):
        respuesta = self.client.post(
            reverse('contacto'),
            {
                'nombre': 'Ana Pérez',
                'correo': 'ana@example.com',
                'telefono': '',
                'asunto': 'Consulta',
                'producto_interes': '',
                'mensaje': 'Muy corto.',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(ConsultaCliente.objects.count(), 0)

    def test_crud_de_productos_requiere_personal_y_crea_producto(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('producto_crear'))
        self.assertEqual(respuesta.status_code, 302)

        administrador = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='ClaveSegura123!',
        )
        self.client.force_login(administrador)
        categoria = Categoria.objects.first()
        respuesta = self.client.post(
            reverse('producto_crear'),
            {
                'nombre': 'Producto de prueba',
                'descripcion': 'Descripción suficiente para probar el alta.',
                'categoria': categoria.pk,
                'precio_clp': 2500,
                'imagen_url': '',
                'stock': 5,
            },
        )

        self.assertRedirects(respuesta, reverse('lista_productos'))
        producto = Producto.objects.get(nombre='Producto de prueba')
        self.assertEqual(
            StockProducto.objects.get(producto_id=producto.pk).stock,
            5,
        )

    def test_reportes_solo_se_muestran_a_personal(self):
        self.client.force_login(self.usuario)
        self.assertEqual(
            self.client.get(reverse('reporte_agrupado')).status_code,
            302,
        )

        administrador = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='ClaveSegura123!',
        )
        self.client.force_login(administrador)
        self.assertEqual(
            self.client.get(reverse('reporte_agrupado')).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse('reporte_stock')).status_code,
            200,
        )
