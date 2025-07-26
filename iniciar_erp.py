#!/usr/bin/env python3
"""
Script para inicializar o ERP de forma automática e prática
Autor: Sistema DVS
"""

import os
import sys
import time
import subprocess
import webbrowser
import threading
from pathlib import Path

# Configurações
PORT = 8000
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}"
LOGIN_URL = f"{URL}/login/?next=/"

def print_banner():
    """Exibe o banner do sistema"""
    print("=" * 60)
    print("           🚀 INICIANDO ERP DVSYSTEM 🚀")
    print("=" * 60)
    print()

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    if sys.version_info < (3, 8):
        print("❌ Erro: Python 3.8 ou superior é necessário!")
        print(f"   Versão atual: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} - OK")
    return True

def check_virtual_env():
    """Verifica se está em um ambiente virtual"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ Ambiente virtual detectado - OK")
    else:
        print("⚠️  Aviso: Não está em um ambiente virtual")
    return True

def install_requirements():
    """Instala as dependências se necessário"""
    try:
        import django
        print("✅ Django já instalado - OK")
        return True
    except ImportError:
        print("📦 Instalando dependências...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True)
            print("✅ Dependências instaladas - OK")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar dependências: {e}")
            return False

def setup_django():
    """Configura o Django"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dvsystem.settings")
    
    try:
        import django
        django.setup()
        print("✅ Django configurado - OK")
        return True
    except Exception as e:
        print(f"❌ Erro ao configurar Django: {e}")
        return False

def check_database():
    """Verifica e prepara o banco de dados"""
    print("🔍 Verificando banco de dados...")
    
    try:
        # Verifica se há migrações pendentes
        result = subprocess.run([sys.executable, "manage.py", "showmigrations", "--plan"], 
                              capture_output=True, text=True)
        
        if "[ ]" in result.stdout:
            print("📊 Aplicando migrações do banco de dados...")
            subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
            print("✅ Migrações aplicadas - OK")
        else:
            print("✅ Banco de dados atualizado - OK")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no banco de dados: {e}")
        return False

def collect_static():
    """Coleta arquivos estáticos"""
    try:
        print("📁 Coletando arquivos estáticos...")
        subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"], 
                      check=True, capture_output=True)
        print("✅ Arquivos estáticos coletados - OK")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Aviso: Erro ao coletar arquivos estáticos (continuando...)")
        return True

def open_browser():
    """Abre o navegador após um delay"""
    time.sleep(3)  # Aguarda o servidor iniciar
    print(f"🌐 Abrindo navegador em {LOGIN_URL}")
    
    # Tenta abrir como PWA no Edge primeiro
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge_proxy.exe"
    if os.path.exists(edge_path):
        try:
            subprocess.Popen([
                edge_path,
                "--profile-directory=Default",
                "--app-id=iplbeaognhfojdbeljdcgcjjehenhepl",
                f"--app-url={LOGIN_URL}",
                "--app-launch-source=4"
            ])
            return
        except:
            pass
    
    # Fallback para navegador padrão
    webbrowser.open(LOGIN_URL)

def start_server():
    """Inicia o servidor Django"""
    print(f"🚀 Iniciando servidor em {URL}")
    print("=" * 60)
    print("   Para parar o servidor, pressione Ctrl+C")
    print("=" * 60)
    print()
    
    try:
        # Inicia o navegador em thread separada
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Inicia o servidor
        subprocess.run([sys.executable, "manage.py", "runserver", f"{HOST}:{PORT}"])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor interrompido pelo usuário")
        print("👋 Obrigado por usar o ERP DVSYSTEM!")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")

def main():
    """Função principal"""
    print_banner()
    
    # Verifica se está no diretório correto
    if not os.path.exists("manage.py"):
        print("❌ Erro: Execute este script no diretório raiz do projeto!")
        print("   (onde está localizado o arquivo manage.py)")
        input("Pressione Enter para sair...")
        return
    
    # Executa verificações
    checks = [
        ("Versão do Python", check_python_version),
        ("Ambiente virtual", check_virtual_env),
        ("Dependências", install_requirements),
        ("Configuração Django", setup_django),
        ("Banco de dados", check_database),
        ("Arquivos estáticos", collect_static),
    ]
    
    print("🔍 Executando verificações do sistema:")
    print("-" * 40)
    
    for name, check_func in checks:
        print(f"Verificando {name}...", end=" ")
        if not check_func():
            print(f"\n❌ Falha na verificação: {name}")
            input("Pressione Enter para sair...")
            return
    
    print("\n✅ Todas as verificações passaram!")
    print("-" * 40)
    print()
    
    # Inicia o servidor
    start_server()

if __name__ == "__main__":
    main()
