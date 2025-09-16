# 📊 IntelliRadar 数据处理流水线使用指南

## 🎯 概述

IntelliRadar 是一个统一的威胁情报数据处理系统，支持从多个数据源自动采集、分析和整合威胁情报数据。系统分为非结构化数据源（需要LLM分析）和结构化数据源（直接处理）两类。

## 🔧 快速开始

### 1. 基本使用

```bash
# 运行完整流水线
python run_pipeline.py

# 查看系统状态
python run_pipeline.py --status

# 查看帮助
python run_pipeline.py --help
```

### 2. 常用命令

```bash
# 只处理非结构化数据源
python run_pipeline.py --sources unstructured

# 只处理结构化数据源
python run_pipeline.py --sources structured

# 处理单个数据源
python run_pipeline.py --source snyk --type unstructured

# 只更新前端数据
python run_pipeline.py --frontend-only

# 列出所有可用数据源
python run_pipeline.py --list-sources
```

## 📊 数据源配置

### 非结构化数据源
需要通过 LLM 进行内容分析和信息提取：

- **snyk** - Snyk 安全博客
- **github_blog** - GitHub 安全博客  
- **threatpost** - Threatpost 安全资讯
- **darkreading** - Dark Reading 网络安全新闻
- **securityweek** - Security Week 安全周刊
- **bleepingcomputer** - BleepingComputer 安全资讯
- **krebsonsecurity** - Krebs on Security 安全博客

### 结构化数据源
可以直接处理的 API 数据源：

- **osv** - OSV 漏洞数据库 (https://osv.dev/)
- **github_advisory** - GitHub Advisory 数据库
- **snyk_vulndb** - Snyk 漏洞数据库

## 🔄 数据处理流程

### 非结构化数据流程
```
📎 采集链接 → 📄 提取内容 → 🤖 LLM分析 → 🔄 数据聚合 → 🎨 前端更新
```

1. **采集链接**: 从各大安全博客网站采集文章链接
2. **提取内容**: 使用爬虫技术提取网页文本内容
3. **LLM分析**: 通过 GPT-4o 进行三步分析
   - `extract`: 提取威胁情报实体
   - `relation`: 分析实体关系
   - `verify`: 验证结果准确性
4. **数据聚合**: 整合、去重、标准化处理
5. **前端更新**: 生成前端可视化数据文件

### 结构化数据流程
```
🔗 API获取 → 📋 数据标准化 → 🔄 数据聚合 → 🎨 前端更新
```

1. **API获取**: 直接从API获取结构化数据
2. **数据标准化**: 转换为统一格式
3. **数据聚合**: 与其他数据源整合
4. **前端更新**: 更新可视化数据

## 📁 目录结构

```
IntelliRadar/
├── Codes/
│   ├── pipeline_config.json      # 流水线配置
│   ├── pipeline_manager.py       # 流水线管理器
│   └── update_frontend_data.py   # 前端数据更新
├── Dataset/
│   ├── Content/                  # 原始内容
│   ├── LLM-Output/              # LLM分析结果
│   └── CSV/                     # 聚合后数据
├── frontend/
│   ├── aggregated_packages.json # 前端主数据
│   └── Intelliradar_data.json  # 统计信息
├── run_pipeline.py             # 主运行脚本
└── PIPELINE_GUIDE.md           # 使用指南
```

## ⚙️ 配置文件

### pipeline_config.json 配置项

```json
{
  "data_sources": {
    "unstructured": {
      "sources": [
        {
          "name": "snyk",
          "enabled": true,
          "collection_method": "snyk_blog",
          "requires_llm": true
        }
      ]
    },
    "structured": {
      "sources": [
        {
          "name": "osv",
          "enabled": true,
          "collection_method": "osv_api",
          "requires_llm": false,
          "api_endpoint": "https://osv.dev/"
        }
      ]
    }
  },
  "pipeline_settings": {
    "max_concurrent_requests": 5,
    "retry_attempts": 3,
    "llm_model": "gpt-4o",
    "enable_deduplication": true,
    "update_frontend": true
  }
}
```

## 🎛️ 高级使用

### 1. 自定义配置

```bash
# 使用自定义配置文件
python run_pipeline.py --config my_config.json
```

### 2. 详细输出模式

```bash
# 详细日志输出
python run_pipeline.py --verbose

# 静默运行
python run_pipeline.py --quiet
```

### 3. 单独更新前端数据

```bash
# 只更新前端数据（不运行其他流程）
python Codes/update_frontend_data.py

# 查看前端数据状态
python Codes/update_frontend_data.py --status
```

## 📈 监控和状态

### 查看系统状态

```bash
python run_pipeline.py --status
```

输出示例：
```
📊 IntelliRadar 系统状态:
============================================================
🕐 更新时间: 2024-12-28T15:30:45
📁 内容文件: 15432 个
🤖 LLM输出: 46296 个  
📊 CSV大小: 2583920 字节

📋 数据源状态:
  ✅ 🔍 🤖 snyk                 - 最后处理: 2024-12-28 14:25
  ✅ 🔍 🤖 github_blog          - 最后处理: 2024-12-28 14:30
  ✅ 📋 📄 osv                  - 最后处理: 2024-12-28 15:15
```

图例：
- ✅/❌ - 启用/禁用
- 🔍 - 非结构化数据源
- 📋 - 结构化数据源  
- 🤖 - 需要LLM分析
- 📄 - 直接处理

## 🔧 故障排除

### 常见问题

1. **配置文件错误**
   ```bash
   ❌ 配置文件不存在: Codes/pipeline_config.json
   ```
   解决：检查配置文件路径是否正确

2. **模块导入失败**
   ```bash
   ❌ 无法导入WebPageCollection: No module named 'webpagecollection'
   ```
   解决：检查相关模块是否存在，确保代码目录结构正确

3. **权限问题**
   ```bash
   ❌ 前端数据更新失败: Permission denied
   ```
   解决：检查输出目录的写入权限

### 日志文件

系统日志保存在 `logs/` 目录下：
- `logs/pipeline_YYYYMMDD.log` - 主要运行日志

## 🎯 最佳实践

1. **定期运行**: 建议每天运行一次完整流水线
2. **增量更新**: 对于新增数据源，先进行单源测试
3. **监控状态**: 定期检查系统状态，确保数据更新正常
4. **备份数据**: 定期备份 `Dataset/CSV/integrity.csv` 数据文件
5. **配置调优**: 根据系统性能调整并发数量和重试次数

## 🤝 扩展开发

### 添加新的数据源

1. **非结构化数据源**:
   - 在 `WebPageCollection` 类中添加采集方法
   - 在 `WebPageContent` 类中添加内容提取方法
   - 在配置文件中添加相应配置

2. **结构化数据源**:
   - 实现 API 调用方法
   - 添加数据标准化逻辑
   - 在配置文件中添加 API 端点配置

### 自定义处理逻辑

可以继承 `PipelineManager` 类并重写相关方法来实现自定义处理逻辑。

---

## 📞 技术支持

如果遇到问题或需要技术支持，请：

1. 检查日志文件获取详细错误信息
2. 确认配置文件格式正确
3. 验证系统依赖是否完整安装

---

*IntelliRadar - 让威胁情报收集变得简单高效* 🚀

