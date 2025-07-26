# Script para remover BOM dos arquivos JSON
for fname in ["backup_clientes_utf8.json", "backup_produtos_utf8.json"]:
    with open(fname, "r", encoding="utf-8-sig") as f:
        data = f.read()
    with open(fname.replace("_utf8", "_utf8_nobom"), "w", encoding="utf-8") as f:
        f.write(data)
print("Arquivos salvos sem BOM.")
