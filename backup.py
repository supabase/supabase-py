import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path

import django
from django.conf import settings

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dvsystem.settings")
django.setup()


def backup_database():
    """Realiza backup do banco de dados."""
    try:
        # Criar diretório de backup se não existir
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)

        # Nome do arquivo de backup
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"db_backup_{timestamp}.sql"

        # Comando para backup do PostgreSQL
        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
            db = settings.DATABASES["default"]
            cmd = [
                "pg_dump",
                "-h",
                db["HOST"],
                "-p",
                str(db["PORT"]),
                "-U",
                db["USER"],
                "-F",
                "c",  # Formato customizado
                "-b",  # Incluir objetos grandes
                "-v",  # Verbose
                "-f",
                str(backup_file),
                db["NAME"],
            ]

            # Executar o comando
            subprocess.run(cmd, check=True, env=dict(os.environ, PGPASSWORD=db["PASSWORD"]))
            print(f"Backup do banco de dados realizado com sucesso: {backup_file}")
        else:
            print("Backup do banco de dados não suportado para este tipo de banco.")

    except Exception as e:
        print(f"Erro ao realizar backup do banco de dados: {e}")


def backup_media():
    """Realiza backup dos arquivos de mídia."""
    try:
        # Criar diretório de backup se não existir
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)

        # Nome do arquivo de backup
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"media_backup_{timestamp}.zip"

        # Criar arquivo ZIP com os arquivos de mídia
        shutil.make_archive(str(backup_file).replace(".zip", ""), "zip", settings.MEDIA_ROOT)
        print(f"Backup dos arquivos de mídia realizado com sucesso: {backup_file}")

    except Exception as e:
        print(f"Erro ao realizar backup dos arquivos de mídia: {e}")


def cleanup_old_backups():
    """Remove backups antigos (mantém apenas os últimos 7 dias)."""
    try:
        backup_dir = Path(settings.BASE_DIR) / "backups"
        if not backup_dir.exists():
            return

        # Data limite (7 dias atrás)
        limit_date = datetime.datetime.now() - datetime.timedelta(days=7)

        # Remover backups antigos
        for backup_file in backup_dir.glob("*"):
            if backup_file.is_file():
                file_date = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_date < limit_date:
                    backup_file.unlink()
                    print(f"Backup antigo removido: {backup_file}")

    except Exception as e:
        print(f"Erro ao limpar backups antigos: {e}")


def main():
    """Função principal."""
    print("Iniciando processo de backup...")

    # Realizar backups
    backup_database()
    backup_media()

    # Limpar backups antigos
    cleanup_old_backups()

    print("Processo de backup concluído.")


if __name__ == "__main__":
    main()
