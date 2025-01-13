from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from django.core.exceptions import ValidationError

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    nombreCompleto = forms.CharField(required=True, label="Nombre completo")
    fotoDePerfil = forms.ImageField(required=False, label="Foto de perfil")
    bio = forms.CharField(
        required=False, 
        label="Biografía",
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Una breve descripción sobre ti"
    )

    class Meta:
        model = Usuario
        fields = ['username', 'nombreCompleto', 'email', 'fotoDePerfil', 'bio']

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        usuario.nombreCompleto = self.cleaned_data['nombreCompleto']
        usuario.bio = self.cleaned_data['bio']
        if 'fotoDePerfil' in self.cleaned_data:
            usuario.fotoDePerfil = self.cleaned_data['fotoDePerfil']
        usuario.is_staff = True
        usuario.is_superuser = True
        if commit:
            usuario.save()
        return usuario

class EditarUsuarioForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")
    nombreCompleto = forms.CharField(required=True, label="Nombre completo")
    fotoDePerfil = forms.ImageField(required=False, label="Foto de perfil")
    bio = forms.CharField(
        required=False, 
        label="Biografía",
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Una breve descripción sobre ti"
    )
    password1 = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(render_value=False),
        label="Nueva contraseña"
    )
    password2 = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(render_value=False),
        label="Confirmar nueva contraseña"
    )

    class Meta:
        model = Usuario
        fields = ['username', 'nombreCompleto', 'email', 'fotoDePerfil', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self._original_username = self.instance.username
            # Ensure password fields are empty
            self.initial['password1'] = ''
            self.initial['password2'] = ''

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username == self._original_username:
            return username
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 or password2:
            if not password1:
                raise ValidationError("Por favor ingrese la nueva contraseña")
            if not password2:
                raise ValidationError("Por favor confirme la nueva contraseña")
            if password1 != password2:
                raise ValidationError("Las contraseñas no coinciden")
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get('password1'):
            usuario.set_password(self.cleaned_data['password1'])
        if commit:
            usuario.save()
        return usuario