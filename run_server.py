import os
import sys

from waitress import serve

from dvsystem.wsgi import get_wsgi_application


def main():
    # Define a porta em que o servidor irá rodar
    port = 8000

    # Obtém a aplicação WSGI do Django
    application = get_wsgi_application()

    # Inicia o servidor Waitress
    print(f"Iniciando servidor na porta {port}...")
    print(f"Acesse a aplicação em http://localhost:{port}")

    serve(application, host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Adiciona o diretório do projeto ao path do Python
    # Isso é necessário para que o PyInstaller encontre os módulos do Django
    project_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_path)

    # Define a variável de ambiente para as configurações do Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dvsystem.settings")

    main()
