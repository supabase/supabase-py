import csv
import os
import sqlite3

# Caminho do banco antigo
DB_ANTIGO = "db_antigo.sqlite3"
EXPORT_DIR = "temp/export_antigo"

# Tabelas a exportar
TABELAS = [
    ("pedidos_pedido", "pedidos_antigos.csv"),
    ("pedidos_itempedido", "itens_pedidos_antigos.csv"),
    # Adicione outras tabelas se necessário, ex: históricos, anexos
]


def exportar_tabela(nome_tabela, nome_csv):
    conn = sqlite3.connect(DB_ANTIGO)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {nome_tabela}")
    colunas = [desc[0] for desc in cursor.description]
    os.makedirs(EXPORT_DIR, exist_ok=True)
    caminho_csv = os.path.join(EXPORT_DIR, nome_csv)
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(colunas)
        for row in cursor.fetchall():
            writer.writerow(row)
    print(f"Exportado: {nome_tabela} -> {caminho_csv}")
    conn.close()


def main():
    for tabela, arquivo in TABELAS:
        exportar_tabela(tabela, arquivo)
    print("Exportação concluída.")


if __name__ == "__main__":
    main()
