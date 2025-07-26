import os
import subprocess
import time


def executar_comando_psql(comando):
    """Executa um comando SQL usando psql"""
    try:
        # Caminho do PostgreSQL
        psql_path = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"

        # Comando completo (sem senha, usando trust)
        cmd = f'"{psql_path}" -U postgres -c "{comando}"'

        # Executa o comando
        resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if resultado.returncode == 0:
            return True
        else:
            print(f"Erro: {resultado.stderr}")
            return False
    except Exception as e:
        print(f"Erro ao executar comando: {e}")
        return False


def configurar_banco():
    print("Iniciando configuração do banco de dados PostgreSQL...")

    # Primeiro, vamos parar o serviço do PostgreSQL
    print("Parando o serviço do PostgreSQL...")
    subprocess.run("net stop postgresql-x64-17", shell=True)
    time.sleep(2)

    # Edita o arquivo pg_hba.conf para permitir conexão sem senha
    pg_hba_path = r"C:\Program Files\PostgreSQL\17\data\pg_hba.conf"
    try:
        with open(pg_hba_path, "r") as f:
            conteudo = f.read()

        # Substitui a linha de autenticação
        conteudo = conteudo.replace(
            "host    all             all             127.0.0.1/32            scram-sha-256",
            "host    all             all             127.0.0.1/32            trust",
        )

        with open(pg_hba_path, "w") as f:
            f.write(conteudo)

        print("Arquivo pg_hba.conf atualizado com sucesso!")
    except Exception as e:
        print(f"Erro ao editar pg_hba.conf: {e}")
        return

    # Inicia o serviço novamente
    print("Iniciando o serviço do PostgreSQL...")
    subprocess.run("net start postgresql-x64-17", shell=True)
    time.sleep(2)

    # Comandos para executar
    comandos = [
        # Altera a senha do postgres
        "ALTER USER postgres WITH PASSWORD '123';",
        # Desconecta usuários e remove banco existente
        "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'dvsystem' AND pid <> pg_backend_pid();",
        "DROP DATABASE IF EXISTS dvsystem;",
        "DROP USER IF EXISTS dvsystem;",
        # Cria usuário e banco
        "CREATE USER dvsystem WITH PASSWORD '123';",
        "CREATE DATABASE dvsystem;",
        "GRANT ALL PRIVILEGES ON DATABASE dvsystem TO dvsystem;",
        # Conecta ao banco e configura permissões
        "\\c dvsystem",
        "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dvsystem;",
        "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dvsystem;",
    ]

    # Executa cada comando
    for comando in comandos:
        print(f"Executando: {comando}")
        if not executar_comando_psql(comando):
            print("Falha ao executar comando. Tentando continuar...")
            time.sleep(1)

    # Restaura a configuração original do pg_hba.conf
    try:
        with open(pg_hba_path, "r") as f:
            conteudo = f.read()

        conteudo = conteudo.replace(
            "host    all             all             127.0.0.1/32            trust",
            "host    all             all             127.0.0.1/32            scram-sha-256",
        )

        with open(pg_hba_path, "w") as f:
            f.write(conteudo)

        print("Configuração de segurança restaurada!")
    except Exception as e:
        print(f"Erro ao restaurar pg_hba.conf: {e}")

    # Reinicia o serviço uma última vez
    subprocess.run("net stop postgresql-x64-17", shell=True)
    time.sleep(2)
    subprocess.run("net start postgresql-x64-17", shell=True)
    time.sleep(2)

    # Cria arquivo .env
    env_content = """# Database settings
DB_NAME=dvsystem
DB_USER=dvsystem
DB_PASSWORD=123
DB_HOST=localhost
DB_PORT=5432

# Django settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
"""

    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("Arquivo .env criado com sucesso!")
    except Exception as e:
        print(f"Erro ao criar arquivo .env: {e}")

    print("\nConfiguração concluída!")
    print("\nPróximos passos:")
    print("1. Verifique se o arquivo .env foi criado corretamente")
    print("2. Execute 'python manage.py migrate' para criar as tabelas")
    print("3. Execute 'python manage.py createsuperuser' para criar um usuário administrador")


if __name__ == "__main__":
    configurar_banco()
