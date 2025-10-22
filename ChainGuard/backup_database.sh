#!/bin/bash

# MongoDB备份脚本
# 备份intelliradar数据库到本地指定目录

# 配置变量
CONTAINER_NAME="ChainGuard-Database"
DATABASE_NAME="intelliradar"
BACKUP_DIR="/home/dev/ChainGuard/Intelliradar/database"
BACKUP_NAME="intelliradar"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker容器是否运行
check_container() {
    log_info "检查MongoDB容器状态..."
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        log_error "MongoDB容器 '$CONTAINER_NAME' 未运行"
        exit 1
    fi
    log_info "MongoDB容器运行正常"
}

# 创建备份目录
create_backup_dir() {
    log_info "创建备份目录: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    if [ $? -ne 0 ]; then
        log_error "无法创建备份目录: $BACKUP_DIR"
        exit 1
    fi
}

# 清理旧备份（如果存在）
cleanup_old_backup() {
    if [ -d "$BACKUP_DIR/$BACKUP_NAME" ]; then
        log_warn "发现旧备份，正在清理..."
        rm -rf "$BACKUP_DIR/$BACKUP_NAME"
        log_info "旧备份已清理"
    fi
}

# 执行备份
perform_backup() {
    log_info "开始备份数据库 '$DATABASE_NAME'..."
    

    # 直接备份到指定的目标路径，避免多层目录问题
    # 方法1: 使用mongodump直接指定输出路径
    docker exec "$CONTAINER_NAME" mongodump --db "$DATABASE_NAME" --out "/tmp/backup"
    
    if [ $? -ne 0 ]; then
        log_error "数据库备份失败"
        exit 1
    fi
    
    log_info "数据库备份完成，正在复制到本地..."
    
    # 方法2: 复制目录内容而不是目录本身
    # 使用 /. 语法复制目录内容到目标位置
    docker cp "$CONTAINER_NAME:/tmp/backup/$DATABASE_NAME/." "$BACKUP_DIR/$BACKUP_NAME/"
    
    if [ $? -ne 0 ]; then
        log_error "复制备份文件失败"
        exit 1
    fi
    
    # 清理容器内的临时备份文件
    docker exec "$CONTAINER_NAME" rm -rf /tmp/backup
    
    log_info "备份文件已复制到: $BACKUP_DIR/$BACKUP_NAME"
}

# 验证备份
verify_backup() {
    log_info "验证备份文件..."
    
    if [ ! -d "$BACKUP_DIR/$BACKUP_NAME" ]; then
        log_error "备份目录不存在"
        exit 1
    fi
    
    # 检查备份文件数量
    file_count=$(find "$BACKUP_DIR/$BACKUP_NAME" -name "*.bson" | wc -l)
    log_info "备份包含 $file_count 个BSON文件"
    
    # 显示备份目录大小
    backup_size=$(du -sh "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
    log_info "备份大小: $backup_size"
    
    # 列出备份的集合
    log_info "备份的集合:"
    ls -la "$BACKUP_DIR/$BACKUP_NAME"/*.bson 2>/dev/null | awk '{print $9}' | sed 's/.*\///' | sed 's/\.bson$//' || log_warn "未找到BSON文件"
}

# 主函数
main() {
    log_info "=== MongoDB数据库备份脚本 ==="
    log_info "容器名称: $CONTAINER_NAME"
    log_info "数据库名称: $DATABASE_NAME"
    log_info "备份目录: $BACKUP_DIR"
    log_info "备份名称: $BACKUP_NAME"
    echo
    
    check_container
    create_backup_dir
    cleanup_old_backup
    perform_backup
    verify_backup
    
    echo
    log_info "=== 备份完成 ==="
    log_info "备份位置: $BACKUP_DIR/$BACKUP_NAME"
    log_info "您可以使用以下命令恢复数据库:"
    echo "docker exec $CONTAINER_NAME mongorestore --db $DATABASE_NAME --drop /path/to/backup/$BACKUP_NAME"
}

# 执行主函数
main "$@"
