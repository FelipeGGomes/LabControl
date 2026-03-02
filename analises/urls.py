from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    
    path('', views.index, name='index'),
    path('parametros/', views.cadastro_parametro, name='cadastro_parametro'),
    path('parametros/editar/<int:id>/', views.editar_parametro, name='editar_parametro'),
    path('parametros/excluir/<int:id>/', views.excluir_parametro, name='excluir_parametro'),
    path('analises/', views.analises, name='analises'),
    path('relatorio/', views.relatorio, name='relatorio'),
    path('relatorio/<int:id>/', views.ver_relatorio, name='ver_relatorio'),
    path('relatorio/<int:id>/atualizar/', views.atualizar_relatorio, name='atualizar_relatorio'),
    path('relatorio/<int:id>/pdf/', views.relatorio_pdf, name='relatorio_pdf'),


    # Rotas de Autenticação nativas
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
   



]