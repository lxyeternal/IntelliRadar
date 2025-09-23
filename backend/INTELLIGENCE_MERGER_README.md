# IntelliRadar Intelligence Merger

智能威胁情报合并系统，用于将从不同数据源采集到的相同包名和版本的威胁情报进行智能合并。

## 🚀 功能特性

### 1. 智能数据拆分
- 自动处理Package Name为列表的情况，拆分为单独的包记录
- 保持原始数据的完整性和关联性

### 2. 多维度合并策略
- **置信度评分**: 基于数据源可靠性和数量进行评分
- **字段合并**: 不同类型字段采用不同的合并策略
- **时间优先**: 优先采用最新的数据

### 3. 数据源可信度分级
- **高可信度源** (100%): github, snykdb, osv
- **其他数据源**: 根据出现频率计算置信度

### 4. 标准化输出格式
- 统一的JSON Schema输出
- 完整的元数据信息
- 可追溯的数据源信息

## 📊 合并后的数据结构

```json
{
  "id": "IR-20241223-npm-a7b3c8d2",
  "package_name": "malicious-package",
  "package_manager": "npm",
  "package_versions": ["1.0.0", "1.0.1"],
  "repository_url": "https://npmjs.com/package/malicious-package",
  
  "credit": {
    "sources": [
      {
        "discoverer": "Security Team",
        "data_source": "github",
        "discovery_date": "2024-12-23T00:00:00Z",
        "source_link": "https://github.com/advisories/GHSA-xxxx"
      }
    ],
    "collected_at": "2024-12-23T20:54:42Z"
  },
  
  "references": [
    {
      "url": "https://github.com/advisories/GHSA-xxxx",
      "type": "github"
    }
  ],
  
  "threat_info": {
    "attack_methods": ["Cryptomining", "Data Exfiltration"],
    "attack_vectors": ["npm postinstall script"],
    "targets": ["Node.js applications"],
    "severity": "high"
  },
  
  "patch_info": {
    "fix_method": "Remove package and use alternative"
  },
  
  "indicators_of_compromise": [
    "http://malicious-domain.com/payload"
  ],
  
  "metadata": {
    "last_updated": "2024-12-23T20:54:42Z",
    "data_quality_score": 0.95,
    "confidence_level": "high",
    "source_count": 3,
    "high_confidence_sources": 2
  }
}
```

## 🛠 使用方法

### 1. 命令行使用

```bash
# 只运行爬虫
python main.py crawl --sources github snykdb

# 只运行合并器
python main.py merge

# 运行爬虫并自动合并
python main.py crawl --auto-merge

# 运行完整流程（推荐）
python main.py full --sources github snykdb osv
```

### 2. 程序化调用

```python
from database.mongodb_manager import MongoDBManager
from analysis.intelligence_merger import IntelligenceMerger

# 初始化
db_manager = MongoDBManager()
merger = IntelligenceMerger(db_manager)

# 执行合并
merged_results = merger.merge_intelligence_data()

# 保存结果
saved_count = merger.save_merged_results(merged_results)
```

### 3. 测试脚本

```bash
python test_merger.py
```

## 🧠 合并算法详解

### 1. 数据预处理
- 从MongoDB `analysis` 集合获取 `step="verify"` 的数据
- 处理Package Name为列表的情况，拆分为独立记录
- 数据标准化和清洗

### 2. 分组策略
- 按 `package_manager::package_name` 进行分组
- 同一组内的所有记录将被合并

### 3. 字段合并规则

| 字段类型 | 合并策略 | 示例字段 |
|---------|---------|----------|
| 基础信息 | 保持唯一值 | package_name, package_manager |
| 版本信息 | 去重合并 | package_versions |
| 威胁信息 | 列表合并去重 | attack_methods, attack_vectors |
| 引用链接 | 去重保留所有 | references |
| 修复方法 | 选择最新 | fix_method |

### 4. 置信度计算

```
质量分数 = (高可信度源数量/总源数量) × 0.7 + min(总源数量/5, 1.0) × 0.3

置信度等级:
- high: 质量分数 ≥ 0.8
- medium: 质量分数 ≥ 0.6  
- low: 质量分数 < 0.6
```

## 📈 性能优化

### 1. 批量处理
- 一次性获取所有数据，减少数据库查询
- 内存中完成所有合并操作

### 2. 索引优化
建议在MongoDB中创建以下索引：
```javascript
db.analysis.createIndex({"step": 1})
db.analysis.createIndex({"source": 1, "step": 1})
db.analysis.createIndex({"result.Package Name": 1, "result.Package Manager": 1})
```

### 3. 内存管理
- 使用生成器处理大数据集
- 及时释放不需要的数据结构

## 🔧 配置选项

可以通过修改 `IntelligenceMerger` 类来调整：

```python
# 高可信度数据源
self.high_confidence_sources = {'github', 'snykdb', 'osv'}

# 字段映射关系
self.field_mappings = {
    'attack_methods': ['Attack Method', 'behavior'],
    'attack_vectors': ['Attack Vector', 'overview'],
    # ... 更多映射
}
```

## 🚨 注意事项

1. **数据完整性**: 确保运行合并前已完成数据采集
2. **存储空间**: 合并结果会存储在新的集合中，注意磁盘空间
3. **时间同步**: 确保不同数据源的时间戳格式一致
4. **错误处理**: 监控合并过程中的错误日志

## 🔍 故障排除

### 常见问题

1. **没有数据被合并**
   - 检查数据库中是否有 `step="verify"` 的数据
   - 确认Package Name字段不为空

2. **置信度评分异常**
   - 检查数据源名称是否正确
   - 确认高可信度源列表配置

3. **内存不足**
   - 分批处理大数据集
   - 增加系统内存或使用流式处理

### 调试模式

在代码中添加调试输出：
```python
merger = IntelligenceMerger(db_manager)
merger.debug = True  # 启用调试模式
```

## 📝 更新日志

- **v1.0.0** (2024-12-23): 初始版本，支持基础合并功能
- 支持多数据源智能合并
- 实现置信度评分系统
- 集成到主程序pipeline
