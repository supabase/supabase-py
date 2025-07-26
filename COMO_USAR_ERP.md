# 🚀 Como Usar o ERP DVSYSTEM - Guia Prático

## 📋 Resumo
Este guia mostra como iniciar o ERP DVSYSTEM de forma simples e prática, sem precisar conhecer comandos do Django.

## 🎯 Opções de Inicialização

### 1. **Método Mais Simples** (Recomendado)
```bash
# Execute o arquivo batch:
iniciar_erp_simples.bat
```
- Clique duas vezes no arquivo `iniciar_erp_simples.bat`
- O sistema fará todas as verificações automaticamente
- O navegador abrirá automaticamente no ERP

### 2. **Método com Mais Detalhes**
```bash
# Execute o script Python:
python iniciar_erp.py
```
- Mostra informações detalhadas sobre o processo
- Faz verificações completas do sistema
- Ideal para diagnóstico de problemas

### 3. **Criar Atalho na Área de Trabalho**
```bash
# Execute uma vez para criar o atalho:
python criar_atalho_desktop.py
```
- Cria um atalho "ERP DVSYSTEM.bat" na área de trabalho
- Depois é só clicar duas vezes no atalho para iniciar

## ✅ O que o Sistema Faz Automaticamente

### Verificações Automáticas:
- ✅ Verifica se o Python está instalado
- ✅ Verifica se as dependências estão instaladas
- ✅ Instala dependências faltantes automaticamente
- ✅ Aplica migrações do banco de dados
- ✅ Coleta arquivos estáticos
- ✅ Inicia o servidor Django
- ✅ Abre o navegador automaticamente

### Recursos Incluídos:
- 🌐 Abertura automática do navegador
- 📱 Suporte a PWA (Progressive Web App) no Edge
- 🔄 Fallback para navegador padrão
- 🛡️ Verificações de segurança
- 📊 Relatórios de status detalhados

## 🔧 Requisitos do Sistema

### Obrigatórios:
- **Python 3.8+** instalado
- **Windows 10/11** (para os arquivos .bat)
- Conexão com internet (primeira execução)

### Opcionais:
- **Microsoft Edge** (para melhor experiência PWA)
- **Ambiente virtual Python** (recomendado)

## 🚨 Solução de Problemas

### Problema: "Python não encontrado"
**Solução:**
1. Instale o Python 3.8+ do site oficial
2. Certifique-se de marcar "Add to PATH" durante a instalação
3. Reinicie o terminal/prompt

### Problema: "Erro ao instalar dependências"
**Solução:**
1. Execute como administrador
2. Ou instale manualmente: `pip install -r requirements.txt`

### Problema: "Erro no banco de dados"
**Solução:**
1. O sistema tenta resolver automaticamente
2. Se persistir, execute: `python manage.py migrate`

### Problema: "Porta 8000 já em uso"
**Solução:**
1. Feche outros servidores Django rodando
2. Ou mude a porta no arquivo `iniciar_erp.py` (linha 16)

## 📁 Estrutura dos Arquivos

```
dvsystem/
├── iniciar_erp_simples.bat     # ← CLIQUE AQUI para iniciar
├── iniciar_erp.py              # Script principal
├── criar_atalho_desktop.py     # Cria atalho na área de trabalho
├── manage.py                   # Django (não precisa usar diretamente)
├── requirements.txt            # Dependências (instaladas automaticamente)
└── ...
```

## 🎯 Fluxo de Uso Diário

### Primeira Vez:
1. Execute `python criar_atalho_desktop.py`
2. Clique no atalho criado na área de trabalho

### Uso Diário:
1. Clique duas vezes em "ERP DVSYSTEM.bat" na área de trabalho
2. Aguarde o sistema inicializar
3. O navegador abrirá automaticamente
4. Faça login no sistema
5. Para parar: pressione `Ctrl+C` no terminal

## 🔒 Segurança

- O sistema usa configurações seguras por padrão
- Senhas e chaves estão no arquivo `.env`
- Acesso apenas local (127.0.0.1)
- HTTPS pode ser configurado se necessário

## 📞 Suporte

Se encontrar problemas:
1. Verifique se seguiu todos os passos
2. Execute `python iniciar_erp.py` para diagnóstico detalhado
3. Consulte a seção "Solução de Problemas" acima
4. Entre em contato com o suporte técnico

---

## 🎉 Pronto!

Agora você pode usar o ERP sem precisar conhecer comandos do Django. Basta clicar e usar! 🚀
