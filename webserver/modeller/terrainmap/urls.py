from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('renderModel', views.renderModel, name='renderModel'),
    path('test', views.test, name='test'),
]
