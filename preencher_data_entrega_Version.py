from datetime import date

from pedidos.models import Pedido

# Defina a data desejada para preencher os pedidos sem data de entrega prevista
data_previsao = date.today()  # ou date(2025, 7, 15) por exemplo

# Filtra pedidos onde data_entrega_prevista está nulo
pedidos_sem_data = Pedido.objects.filter(data_entrega_prevista__isnull=True)

print(f"Encontrados {pedidos_sem_data.count()} pedidos sem data de entrega prevista.")

for pedido in pedidos_sem_data:
    pedido.data_entrega_prevista = data_previsao
    pedido.save()
    print(f"Pedido {pedido.pk}: data_entrega_prevista atualizada para {data_previsao}")

print("Pronto! Todos os pedidos sem data de entrega prevista foram atualizados.")
