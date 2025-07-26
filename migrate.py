import os
import subprocess
import sys
from datetime import datetime

import mysql.connector
from mysql.connector import Error


def execute_sql_file(cursor, filename):
    """Executa um arquivo SQL"""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            sql_commands = file.read()
            for command in sql_commands.split(";"):
                if command.strip():
                    cursor.execute(command)
        return True
    except Error as e:
        print(f"Erro ao executar {filename}: {str(e)}")
        return False


def backup_database(host, user, password, database):
    """Faz backup do banco de dados atual"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{database}_{timestamp}.sql"

    try:
        # Comando para fazer o backup
        command = f"mysqldump -h {host} -u {user} -p{password} {database} > {backup_file}"
        subprocess.run(command, shell=True, check=True)
        print(f"Backup criado com sucesso: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        print(f"Erro ao criar backup: {str(e)}")
        return None


def rename_tables(cursor):
    """Renomeia as tabelas antigas adicionando sufixo _old"""
    tables = ["produtos_categoriaproduto", "produtos_produto", "produtos_movimentoestoque", "produtos_historicopreco"]

    try:
        for table in tables:
            cursor.execute(f"RENAME TABLE {table} TO {table}_old")
        print("Tabelas antigas renomeadas com sucesso")
        return True
    except Error as e:
        print(f"Erro ao renomear tabelas: {str(e)}")
        return False


def main():
    # Configurações do banco de dados
    config = {
        "host": "localhost",
        "user": input("Digite o usuário do MySQL: "),
        "password": input("Digite a senha do MySQL: "),
        "database": "dvsystem",
    }

    try:
        # Conecta ao banco de dados
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        print("\nIniciando processo de migração...")

        # 1. Faz backup do banco atual
        print("\n1. Criando backup do banco atual...")
        backup_file = backup_database(**config)
        if not backup_file:
            print("Erro ao criar backup. Abortando migração.")
            return

        # 2. Renomeia as tabelas antigas
        print("\n2. Renomeando tabelas antigas...")
        if not rename_tables(cursor):
            print("Erro ao renomear tabelas. Abortando migração.")
            return

        # 3. Cria o novo banco de dados
        print("\n3. Criando novo banco de dados...")
        if not execute_sql_file(cursor, "database.sql"):
            print("Erro ao criar novo banco. Abortando migração.")
            return

        # 4. Migra os dados
        print("\n4. Migrando dados...")
        if not execute_sql_file(cursor, "migrate_data.sql"):
            print("Erro ao migrar dados. Abortando migração.")
            return

        # Commit das alterações
        connection.commit()
        print("\nMigração concluída com sucesso!")

        # Exibe resumo da migração
        print("\nResumo da migração:")
        cursor.execute("SELECT COUNT(*) FROM produtos_categoriaproduto")
        print(f"Total de categorias: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM produtos_produto")
        print(f"Total de produtos: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM produtos_movimentoestoque")
        print(f"Total de movimentos: {cursor.fetchone()[0]}")

        cursor.execute("SELECT COUNT(*) FROM produtos_historicopreco")
        print(f"Total de alterações de preço: {cursor.fetchone()[0]}")

    except Error as e:
        print(f"Erro durante a migração: {str(e)}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nConexão com o banco de dados fechada.")


if __name__ == "__main__":
    main()
