from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class RegistroUsuarioForm(UserCreationForm):
  email = forms.EmailField(required=True, label="Email")
  nombreCompleto = forms.CharField(required=True, label="Nombre completo")
  fotoDePerfil = forms.ImageField(required=False, label="Foto de perfil")

  class Meta:
    model = Usuario
    fields = ("username", "nombreCompleto", "email", "fotoDePerfil", "password1", "password2")
    labels = {
      "username": "Nombre de usuario",
      "password1": "Contraseña",
      "password2": "Repetir contraseña"
    }
  
  def save(self, commit=True):
    usuario = super(RegistroUsuarioForm, self).save(commit=False)
    usuario.email = self.cleaned_data['email']
    usuario.nombreCompleto = self.cleaned_data['nombreCompleto']
    if 'fotoDePerfil' in self.cleaned_data:
        usuario.fotoDePerfil = self.cleaned_data['fotoDePerfil']
    if commit:
      print(f"Saving user: {usuario.username}, Email: {usuario.email}")
      usuario.save()
    else:
        print(f"User not saved: {usuario.username}, Commit: {commit}")
    return usuario