from django.shortcuts import render, redirect
from .forms import FotoForm
from django.contrib.auth.decorators import login_required

def inicio(request):
  return render(request, 'inicio.html')

@login_required
def subir_foto(request):
  if request.method == 'POST':
    form = FotoForm(request.POST, request.FILES)
    if form.is_valid():
      foto = form.save(commit=False)
      foto.usuario = request.user
      foto.save()
      return redirect('inicio')
  else:
    form = FotoForm()
  return render(request, 'subir_foto.html', {'form': form})