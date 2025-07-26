import csv
import os
from datetime import datetime

from django.contrib.auth.models import User

from clientes.models import Cliente
from financeiro.models import CentroCusto, Despesa, Receita
from pedidos.models import Pedido

# Ajuste os caminhos conforme necessário
RECEITAS_CSV = "temp/receitas_antigas.csv"
DESPESAS_CSV = "temp/despesas_antigas.csv"


def importar_receitas():
    with open(RECEITAS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            # Ajuste os campos conforme o modelo novo
            cliente = Cliente.objects.filter(pk=row.get("cliente_id")).first() if row.get("cliente_id") else None
            pedido = Pedido.objects.filter(pk=row.get("pedido_id")).first() if row.get("pedido_id") else None
            usuario = User.objects.filter(pk=row.get("usuario_id")).first() if row.get("usuario_id") else None
            receita, created = Receita.objects.get_or_create(
                descricao=row.get("descricao", "")[:255],
                data=row.get("data") or datetime.now().date(),
                valor=row.get("valor") or 0,
                categoria=row.get("categoria") or "pedido",
                cliente=cliente,
                pedido=pedido,
                forma_pagamento=row.get("forma_pagamento") or "dinheiro",
                status=row.get("status") or "P",
                usuario=usuario or User.objects.first(),
            )
            count += 1
        print(f"Importadas {count} receitas.")


def importar_despesas():
    with open(DESPESAS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            centro_custo = (
                CentroCusto.objects.filter(pk=row.get("centro_custo_id")).first()
                if row.get("centro_custo_id")
                else None
            )
            usuario = User.objects.filter(pk=row.get("usuario_id")).first() if row.get("usuario_id") else None
            despesa, created = Despesa.objects.get_or_create(
                descricao=row.get("descricao", "")[:255],
                data=row.get("data") or datetime.now().date(),
                valor=row.get("valor") or 0,
                categoria=row.get("categoria") or "outros",
                centro_custo=centro_custo,
                forma_pagamento=row.get("forma_pagamento") or "dinheiro",
                status=row.get("status") or "P",
                usuario=usuario or User.objects.first(),
            )
            count += 1
        print(f"Importadas {count} despesas.")


if __name__ == "__main__":
    importar_receitas()
    importar_despesas()
