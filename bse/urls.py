from django.urls import path
from .views import bhav_bse

urlpatterns = [
    path('bhav/', bhav_bse, name='bhav_bse'),
]
