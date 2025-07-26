from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("clientes/", include("clientes.urls")),
    path("produtos/", include("produtos.urls")),
    path("pedidos/", include("pedidos.urls")),
    path("financeiro/", include("financeiro.urls")),
    path("agenda/", include("agenda.urls")),
    path("relatorios/", include("relatorios.urls")),
    path("", include("core.urls")),
]
