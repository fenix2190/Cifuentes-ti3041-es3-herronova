from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ConsultaCliente, Producto, StockProducto


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class InicioSesionForm(forms.Form):
    username = forms.CharField(label='Usuario')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)


class ProductoForm(forms.ModelForm):
    stock = forms.IntegerField(min_value=0, label='Stock')

    class Meta:
        model = Producto
        fields = ('nombre', 'descripcion', 'categoria', 'precio_clp', 'imagen_url')
        labels = {
            'precio_clp': 'Precio (CLP)',
            'imagen_url': 'URL de la imagen',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['stock'].initial = StockProducto.objects.filter(
                producto_id=self.instance.pk
            ).values_list('stock', flat=True).first() or 0

    def save(self, commit=True):
        producto = super().save(commit=commit)
        if commit:
            StockProducto.objects.update_or_create(
                producto_id=producto.pk,
                defaults={'stock': self.cleaned_data['stock']},
            )
        return producto


class ConsultaClienteForm(forms.ModelForm):
    class Meta:
        model = ConsultaCliente
        fields = ('nombre', 'correo', 'telefono', 'asunto', 'producto_interes', 'mensaje')
        labels = {
            'correo': 'Correo electrónico',
            'producto_interes': 'Producto de interés',
        }

    def clean_mensaje(self):
        mensaje = self.cleaned_data['mensaje']
        if len(mensaje.strip()) < 20:
            raise forms.ValidationError(
                'El mensaje debe tener al menos 20 caracteres.'
            )
        return mensaje
