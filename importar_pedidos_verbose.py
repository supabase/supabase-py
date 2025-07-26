import json
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dvsystem.settings")
django.setup()

import csv

from django.contrib.auth import get_user_model

from clientes.models import Cliente
from pedidos.models import ItemPedido, Pedido
from produtos.models import Produto
from vendedores.models import Vendedor

User = get_user_model()


def load_json_autoencoding(path):
    for enc in ["utf-8-sig", "utf-8", "utf-16", "latin1"]:
        try:
            with open(path, encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    raise RuntimeError(f"Não foi possível ler {path} com os encodings comuns.")


# Carregar backups para mapear IDs antigos para nomes/descrições
clientes_backup = load_json_autoencoding("backup_clientes.json")
produtos_backup = load_json_autoencoding("backup_produtos.json")

# Mapas de id antigo para nome/descrição
clientes_id_nome = {
    c["pk"]: c["fields"]["nome"].strip().upper() for c in clientes_backup if c["model"].endswith("cliente")
}
produtos_id_desc = {
    p["pk"]: p["fields"]["descricao"].strip().upper() for p in produtos_backup if p["model"].endswith("produto")
}

# Mapas de nome/descrição para instância
clientes_map = {c.nome.strip().upper(): c for c in Cliente.objects.all()}
produtos_map = {p.descricao.strip().upper(): p for p in Produto.objects.all()}
vendedores_map = {v.nome.strip().lower(): v for v in Vendedor.objects.all()}

# Buscar admin padrão
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.filter(username="admin").first()

# Funções de busca


def get_cliente_by_id_antigo(id_antigo):
    nome = clientes_id_nome.get(int(id_antigo or 0), None)
    if nome:
        return clientes_map.get(nome)
    return None


def get_produto_by_id_antigo(id_antigo):
    desc = produtos_id_desc.get(int(id_antigo or 0), None)
    if desc:
        return produtos_map.get(desc)
    return None


def get_vendedor_by_name(nome):
    if not nome:
        return None
    return vendedores_map.get(nome.strip().lower())


def importar_pedidos(csv_file):
    from pedidos.models import CupomDesconto

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["cliente"] = get_cliente_by_id_antigo(row.get("cliente_id"))
                row["usuario"] = admin_user
                row["criado_por"] = admin_user
                row["atualizado_por"] = admin_user
                row["vendedor"] = get_vendedor_by_name(row.get("vendedor"))
                # Cupom: buscar instância ou None
                cupom_val = row.get("cupom")
                if cupom_val:
                    cupom_val = cupom_val.strip()
                if cupom_val:
                    try:
                        row["cupom"] = CupomDesconto.objects.get(codigo=cupom_val)
                    except Exception:
                        row["cupom"] = None
                else:
                    row["cupom"] = None
                # Corrigir campos de data vazios
                campos_data = [
                    "data",
                    "data_entrega_prevista",
                    "data_entrega_realizada",
                    "data_arte_aprovada",
                    "data_sinal_pago",
                    "data_restante_pago",
                    "data_envio",
                    "data_entrega",
                    "criado_em",
                    "atualizado_em",
                ]
                for campo in campos_data:
                    if campo in row and (row[campo] == "" or row[campo] is None):
                        row[campo] = None
                # Remove campos vazios que não são do model
                for k in list(row.keys()):
                    if k not in [f.name for f in Pedido._meta.fields]:
                        row.pop(k)
                if not row["cliente"]:
                    print(
                        f"Cliente não encontrado para pedido: {row.get('codigo')}, id antigo: {row.get('cliente_id')}"
                    )
                    continue
                obj = Pedido(**row)
                obj.save()
            except Exception as e:
                print(f"Erro ao importar Pedido: {row}\nMotivo: {e}")


def importar_itenspedido(csv_file):
    pedidos_map = {p.codigo: p for p in Pedido.objects.all()}
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["produto"] = get_produto_by_id_antigo(row.get("produto_id"))
                pedido_id = row.get("pedido_id")
                # Buscar o código do pedido pelo id antigo
                pedido_obj = None
                for p in pedidos_map.values():
                    if str(p.id) == str(pedido_id):
                        pedido_obj = p
                        break
                row["pedido"] = pedido_obj
                for k in list(row.keys()):
                    if k not in [f.name for f in ItemPedido._meta.fields]:
                        row.pop(k)
                if not row["produto"] or not row["pedido"]:
                    print(f"Produto ou Pedido não encontrado para item: {row}")
                    continue
                obj = ItemPedido(**row)
                obj.save()
            except Exception as e:
                print(f"Erro ao importar ItemPedido: {row}\nMotivo: {e}")


# Importe na ordem correta para respeitar as FK
importar_pedidos("temp/export_antigo/pedidos_antigos.csv")
importar_itenspedido("temp/export_antigo/itens_pedidos_antigos.csv")

print("Importação concluída.")
