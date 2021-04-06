from django.shortcuts import render

# Create your views here.

def bhav_bse(request):
  template_name = 'bhav_bse.html'
  return render(request, template_name, {'bhav_data': 'bhav'})