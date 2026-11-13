"""
URL configuration for catalogo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('catalogo/', views.lista_productos, name='lista_productos'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('producto/<int:producto_id>/comprar/', views.comprar_producto, name='comprar_producto'),
    path('producto/<int:producto_id>/agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/', views.ver_carrito, name='carrito'),
    path('carrito/actualizar/<int:producto_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/vaciar/', views.vaciar_carrito, name='vaciar_carrito'),
    path('carrito/compra/', views.compra, name='compra'),
    path('registro/', views.registro, name='registro'),
    path('iniciar-sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
    path('administrar-stock/', views.administrar_stock, name='administrar_stock'),
    path('producto/nuevo/', views.ProductoCreateView.as_view(), name='producto_crear'),
    path('producto/editar/<int:pk>/', views.ProductoUpdateView.as_view(), name='producto_editar'),
    path('producto/eliminar/<int:pk>/', views.ProductoDeleteView.as_view(), name='producto_eliminar'),
    path('reporte/agrupado/', views.reporte_agrupado, name='reporte_agrupado'),
    path('reporte/stock/', views.reporte_stock_critico, name='reporte_stock'),
    path('contacto/', views.contacto_cliente, name='contacto'),
]
