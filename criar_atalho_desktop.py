#!/usr/bin/env python3
"""
Script para criar um atalho do ERP na área de trabalho
"""

import os
import sys
from pathlib import Path

def criar_atalho_desktop():
    """Cria um atalho na área de trabalho para o ERP"""
    
    # Caminho para a área de trabalho
    desktop = Path.home() / "Desktop"
    
    # Caminho atual do projeto
    projeto_path = Path.cwd()
    
    # Caminho do script batch
    batch_path = projeto_path / "iniciar_erp_simples.bat"
    
    # Caminho do atalho
    atalho_path = desktop / "ERP DVSYSTEM.bat"
    
    try:
        # Garante que o diretório Desktop existe
        desktop.mkdir(exist_ok=True)
        
        # Conteúdo do atalho
        conteudo_atalho = f'''@echo off
cd /d "{projeto_path}"
call "{batch_path}"
'''
        
        # Cria o atalho
        with open(atalho_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_atalho)
        
        print("✅ Atalho criado com sucesso na área de trabalho!")
        print(f"   Localização: {atalho_path}")
        print("\n🚀 Agora você pode iniciar o ERP clicando duas vezes no atalho:")
        print("   'ERP DVSYSTEM.bat' na sua área de trabalho")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar atalho: {e}")
        return False

def main():
    print("=" * 50)
    print("    CRIADOR DE ATALHO - ERP DVSYSTEM")
    print("=" * 50)
    print()
    
    if not os.path.exists("manage.py"):
        print("❌ Erro: Execute este script no diretório raiz do projeto!")
        input("Pressione Enter para sair...")
        return
    
    if not os.path.exists("iniciar_erp_simples.bat"):
        print("❌ Erro: Arquivo 'iniciar_erp_simples.bat' não encontrado!")
        input("Pressione Enter para sair...")
        return
    
    criar_atalho_desktop()
    print()
    input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()
