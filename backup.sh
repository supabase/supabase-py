#!/bin/bash

# Configurações
BACKUP_DIR="/path/to/backups"
DB_NAME="dvsystem"
DB_USER="postgres"
MEDIA_DIR="/path/to/media"
LOG_FILE="/var/log/dvsystem/backup.log"
RETENTION_DAYS=7

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

# Função para logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Backup do banco de dados
backup_database() {
    log "Iniciando backup do banco de dados..."
    BACKUP_FILE="$BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql"
    
    if pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE; then
        log "Backup do banco de dados concluído: $BACKUP_FILE"
        gzip $BACKUP_FILE
    else
        log "ERRO: Falha no backup do banco de dados"
        exit 1
    fi
}

# Backup dos arquivos de mídia
backup_media() {
    log "Iniciando backup dos arquivos de mídia..."
    BACKUP_FILE="$BACKUP_DIR/media_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    if tar -czf $BACKUP_FILE -C $(dirname $MEDIA_DIR) $(basename $MEDIA_DIR); then
        log "Backup dos arquivos de mídia concluído: $BACKUP_FILE"
    else
        log "ERRO: Falha no backup dos arquivos de mídia"
        exit 1
    fi
}

# Limpar backups antigos
cleanup_old_backups() {
    log "Limpando backups antigos..."
    find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete
    log "Limpeza concluída"
}

# Função principal
main() {
    log "Iniciando processo de backup..."
    
    # Realizar backups
    backup_database
    backup_media
    
    # Limpar backups antigos
    cleanup_old_backups
    
    log "Processo de backup concluído"
}

# Executar função principal
main 