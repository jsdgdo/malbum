from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistroUsuarioForm

def registrarUsuario(request):
  if request.method == "POST":
    form = RegistroUsuarioForm(request.POST, request.FILES)
    if form.is_valid():
      usuario = form.save()
      login(request, usuario)
      return redirect("inicio")
    else: 
      print (form.errors)
  else:
    form = RegistroUsuarioForm()
  return render(request, "usuario/registrar.html", {"form": form})
