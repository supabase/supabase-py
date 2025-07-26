import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dvsystem.settings")
import django

django.setup()
from django.db import transaction

from pedidos.models import Pedido
from vendedores.models import Vendedor

# Cria vendedores para todos os nomes distintos já existentes nos pedidos
vendedores_nomes = set(Pedido.objects.values_list("vendedor", flat=True))
vendedores_nomes = {nome for nome in vendedores_nomes if nome and nome.strip()}

with transaction.atomic():
    for nome in vendedores_nomes:
        vendedor, created = Vendedor.objects.get_or_create(nome=nome.strip())
        if created:
            print(f"Vendedor criado: {vendedor.nome}")

print("Criação de vendedores concluída. Agora altere o campo vendedor para ForeignKey e prossiga com as migrações.")
