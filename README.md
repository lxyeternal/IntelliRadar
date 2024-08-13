# IntelliRadar Project

## 项目简介

IntelliRadar 是一个用于从开源数据源中采集与包管理器情报相关网页信息的项目。该项目通过采集多个情报源（如博客、新闻网站、社交媒体等）的信息，利用大语言模型（LLM）的“Least to Most”提示工程（LtM）来提取情报实体、分析实体关系并验证这些信息。最终，通过投票机制聚合来自不同情报源的情报，以提供更加可靠和综合的情报数据。

## 工作流程

IntelliRadar 的工作流程分为以下几个主要步骤：

1. **情报源识别**
   - 通过关键词提取和搜索引擎滚雪球方法确定情报源。

2. **网页文本采集**
   - 从多个情报源中采集与包管理器相关的网页内容，包括从 Twitter 和 Reddit 等社交媒体中采集相关内容。

3. **情报实体抽取**
   - 使用 LLM 的 LtM 提示工程，从采集到的文本内容中提取情报实体，并进一步分析实体间的关系。

4. **情报聚合**
   - 通过投票机制，聚合不同情报源中的情报实体，并解析生成的 JSON 文件，最终输出经过处理的情报数据。

## 文件结构

项目的目录结构如下：


### 主要目录和文件说明

```bash
- **Codes**: 包含主要的代码逻辑，包括数据采集、分析和聚合。
  - **Aggregate**: 包含情报数据的聚合和投票机制代码。
    - `dataintegrity.py`: 解析 LLM 提取的 JSON 文件并聚合情报。
    - `intellivote.py`: 实现情报实体聚合的投票机制。
  - **Collection**: 包含网页采集和数据提取的代码。
    - `reddit_collect.py`: 采集 Reddit 中与包管理器恶意情报相关的内容。
    - `twitter-scraper/`: 采集 Twitter 上安全研究员发布的相关内容。
    - `webpage_collection.py`: 采集情报源下的历史和最新帖子链接。
    - `webpage_content.py`: 采集帖子的文本内容。
  - **GPTAnalysis**: 包含情报实体的抽取与分析逻辑。
    - `lstgptuse.py`: 利用 LtM 提示工程完成文本中的情报实体抽取。
  - **IntelliSource**: 包含确定情报源的方法和相关代码。
    - `google_search.py`, `googleurl_analysis.py`: 通过搜索引擎和关键词滚雪球方法确定情报源。
  - **Keywords**: 包含关键词提取和处理的相关代码。利用聚类算法和 TF-IDF 提取用于检索的通用和特定关键词。
  - **Downstream**: 包含与下游分析相关的工具代码。
    - `scan_mirrors.py`: 扫描并分析恶意包管理器镜像。

- **Configs**: 包含项目的配置文件和初始化代码。
  - `config.json`: 项目的配置文件。

- **Dataset**: 包含采集和处理后的数据文件。
  - **Content**: 从网页中采集到的网页文本。
  - **Json**: 通过 LLM 提取的实体文件。
  - **CSV**: 最终提取到的情报文件。

- **archive**: 存档数据文件。
- **utils**: 包含实用工具，如 `chromedriver`。
```

## 环境配置

### 环境依赖

在运行本项目之前，请确保你已安装以下依赖项：

```bash
pip install -r requirements.txt
```

### 配置文件
在 Configs 目录下的 config.json 文件中，你可以配置项目的关键参数，例如数据路径、API 密钥等。

### 驱动配置
utils/chromedriver/ 目录下包含了不同操作系统的 chromedriver 文件。请确保选择并配置与你的操作系统相匹配的驱动文件。

## 使用说明
### 运行项目
你可以通过运行 main.py 来启动整个情报采集与分析流程：

```bash
python Codes/main.py
```
