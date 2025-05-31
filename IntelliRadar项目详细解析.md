# IntelliRadar项目详细解析

## 项目概述

IntelliRadar是一个智能情报收集与分析系统，专注于从开源数据源中采集与包管理器安全相关的情报。该项目通过系统化的流程，从多个情报源（如安全博客、技术网站、社交媒体等）收集信息，利用大语言模型（LLM）的"Least to Most"提示工程（LtM）技术提取情报实体，分析实体关系，并通过投票机制聚合来自不同情报源的情报，最终提供更加可靠和综合的情报数据。

## 核心功能

- **多源情报采集**：从多个技术博客、社交媒体平台自动获取与包管理器安全相关的文章和讨论
- **智能情报提取**：利用LLM技术智能识别和提取文本中的情报实体和关系
- **数据整合与验证**：对提取的情报进行验证和整合，提高情报可靠性
- **结构化数据输出**：将处理后的情报以结构化的形式（如CSV）输出，便于后续应用

## 系统架构

### 整体架构

IntelliRadar采用模块化的系统架构，主要包括以下几个核心模块：

1. **情报源识别模块**：确定和管理情报来源
2. **网页采集模块**：从情报源爬取内容
3. **内容提取模块**：从网页中提取文本内容
4. **情报分析模块**：使用LLM技术从文本中提取情报实体和关系
5. **情报聚合模块**：整合和验证从不同来源提取的情报

### 数据流向

数据在系统中的流向如下：

```
情报源(博客/社交媒体) → 网页链接采集 → 网页内容提取 → LLM情报实体提取 → 情报聚合与验证 → 结构化数据输出
```

## 详细实现流程

### 1. 情报源识别与管理

项目通过`IntelliSource`模块，使用关键词搜索和滚雪球方法来确定信息来源：

- **关键词提取**：使用自定义关键词列表搜索潜在的情报源
- **源管理**：系统可以跟踪和管理多个情报源，包括技术博客（如Snyk、JFrog等）和社交媒体平台（如Reddit、Twitter）

### 2. 网页链接采集

`Collection`模块中的`WebPageCollection`类负责从各情报源采集历史和最新的文章链接：

- **支持多种网站结构**：为不同博客平台定制采集方法（如`snyk_blog`、`github_blog`等）
- **增量采集**：记录已处理的链接，避免重复采集
- **链接存储**：将待采集的链接存储在`waiting_collection.txt`中，已采集的链接存储在`collected_pagelinks.txt`中

代码示例：
```python
def bleepingcomputer_blog(self):
    for page_index in range(1, 3):
        if page_index == 1:
            pageurl = "https://www.bleepingcomputer.com/tag/pypi/"
        else:
            pageurl = self.bleepingcomputer.format(page_index)
        self.driver.get(pageurl)
        # 提取网页中的链接和日期
        # ...
        if li_url not in self.old_webpage_dict.get("bleepingcomputer_oss", []):
            self.write_txt("bleepingcomputer_oss", formatted_date, li_url)
```

### 3. 网页内容提取

`WebPageContent`类负责从采集到的链接中提取文本内容：

- **针对性提取**：为每个情报源定制内容提取方法（如`medium_content`、`snyk_content`等）
- **多元素解析**：能够处理不同类型的HTML元素，如表格、列表、代码块等
- **内容存储**：将提取的内容保存到`Dataset/Content/{source}/{timestamp}.txt`文件中

代码示例：
```python
def snyk_content(self, timestamp, url):
    try:
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.get(url)
        # 等待页面加载并提取内容元素
        # ...
        page_content = self.parse_elements(driver, article, timestamp)
        content_file = os.path.join(self.text_dir, "snyk", f"{timestamp}.txt")
        self.write_text(page_content, content_file)
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
```

### 4. 情报实体提取

`GPTAnalysis`模块中的`LTMGPT`类使用大语言模型进行情报实体提取：

- **Least to Most提示工程**：采用分步骤的方式引导LLM进行情报提取
- **三步分析流程**：
  1. **实体提取**：从文本中识别关键情报实体（如包名、攻击方法等）
  2. **关系分析**：分析实体之间的关系（如某包使用了什么攻击方法）
  3. **信息验证**：验证提取的信息的准确性和完整性
- **结果序列化**：将提取结果以JSON格式保存

代码示例：
```python
def process_content(self, source, content_file_path, content_file_name):
    # 读取文本内容
    content = self.read_txt(content_file_path)
    
    # 使用LLM进行三步分析
    model = "gpt-4o"
    prompt_type = "cot"  # Chain of Thought
    
    # 1. 提取实体
    extract_prompt = self.get_prompt("extract", prompt_type)
    extracted_entity = self.entity_extract_llm(content, [], model, extract_prompt)
    
    # 2. 分析关系
    relation_prompt = self.get_prompt("relation", prompt_type)
    entity_relation = self.entity_realtion_llm(content, extracted_entity, model, relation_prompt)
    
    # 3. 验证信息
    verify_prompt = self.get_prompt("verify", prompt_type)
    verified_info = self.info_verify_llm(content, entity_relation, model, verify_prompt)
    
    # 保存结果
    timestamp = content_file_name.split('.')[0]
    json_file_path = os.path.join(self.json_dir, source, f"{timestamp}_verify_gpt4.json")
    self.save_json(verified_info, json_file_path)
```

### 5. 情报聚合与验证

`Aggregate`模块中的`DataIntegrity`类负责处理和聚合提取的情报：

- **JSON解析**：解析LLM生成的JSON格式情报
- **数据标准化**：处理不同格式的数据，统一为标准格式
- **CSV输出**：将处理后的情报保存为CSV格式，便于后续分析和应用

代码示例：
```python
def parse_json_file(self, file_path):
    data_timestamp = self.parse_timestamp(file_path)
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
        file_content = self.remove_json_comments(file_content)
        data = json.loads(file_content)
        
        # 解析处理JSON数据
        parsed_data = []
        for item in data:
            # 处理包名、攻击方法等字段
            # ...
            parsed_entry = {
                "Package Name": package_name,
                "Package Manager": item.get("Package Manager", ""),
                # 其他字段...
                "Source": self.intellisource
            }
            parsed_data.append(parsed_entry)
        return parsed_data
```

## 流程示例分析

以下是IntelliRadar处理一篇情报源文章的完整流程示例：

1. **链接采集**：系统从Snyk博客采集到一篇关于包管理器安全的文章链接
2. **内容提取**：系统从链接中提取文章内容，保存为`snyk_88.txt`
3. **情报分析**：LLM分析文章内容，识别出涉及的包名（notevil、argencoders-notevil和libxmljs）、攻击方法（Prototype Pollution和Type Confusion）等情报实体
4. **关系建立**：确定实体间关系，如notevil包存在Prototype Pollution漏洞，CVE编号为CVE-2021-23771
5. **数据整合**：系统将分析结果保存为JSON文件`snyk_88_gpt4.json`
6. **格式转换**：最终将结果转换为CSV格式，包含包名、包管理器、版本等标准字段

## 文件结构

项目的主要文件结构如下：

```
├── Codes
│   ├── Aggregate          # 情报聚合与验证模块
│   │   ├── dataintegrity.py  # JSON解析与CSV输出
│   │   └── intellivote.py    # 情报聚合投票机制
│   ├── Collection         # 网页采集模块
│   │   ├── webpage_collection.py  # 链接采集
│   │   └── webpage_content.py     # 内容提取
│   ├── GPTAnalysis        # 情报分析模块
│   │   ├── lst-gptuse.py         # LLM情报提取
│   │   └── LtM_prompts/          # 提示工程模板
│   ├── IntelliSource      # 情报源识别模块
│   │   ├── google_search.py      # 搜索引擎采集
│   │   └── googleurl_analysis.py # URL分析
│   ├── Keywords           # 关键词处理模块
│   └── main.py            # 主程序入口
├── Configs
│   └── config.json        # 配置文件
└── Dataset                # 数据存储
    ├── Content            # 提取的网页内容
    ├── Json               # LLM分析的JSON结果
    └── CSV                # 最终的CSV格式情报
```

## 关键技术分析

### 1. Least to Most提示工程（LtM）

IntelliRadar使用LtM提示工程技术引导LLM分析情报：

- **步骤分解**：将复杂任务分解为多个简单步骤
- **渐进式分析**：从简单的实体识别到复杂的关系分析，逐步深入
- **结果验证**：通过特定提示引导LLM自我验证结果

### 2. 爬虫技术与反爬虫策略

系统采用多种技术实现稳定的网页采集：

- **Selenium+BeautifulSoup组合**：使用Selenium处理动态加载内容，BeautifulSoup解析HTML
- **反爬虫绕过**：模拟真实浏览器行为，避免被目标网站识别为爬虫
- **增量式采集**：记录已采集的链接，避免重复处理

### 3. 情报实体聚合

通过整合多个情报源的信息，提高情报的可靠性：

- **一致性验证**：比较不同来源的相同实体信息
- **补充完善**：不同来源可能提供互补信息，系统能够整合这些信息
- **结构化输出**：标准化的输出格式便于后续分析和应用

## 应用场景

IntelliRadar系统可应用于多个安全相关场景：

1. **软件供应链安全监控**：及时发现和响应包管理器中的安全威胁
2. **漏洞情报收集**：自动收集开源组件的漏洞信息
3. **安全研究与分析**：为安全研究人员提供结构化的情报数据
4. **风险评估**：评估软件依赖中的潜在安全风险

## 系统优势

1. **自动化程度高**：从情报源识别到情报聚合的全流程自动化
2. **适应性强**：可轻松扩展支持新的情报源和数据格式
3. **情报质量高**：通过LLM和多源聚合提高情报准确性
4. **实时性好**：能够及时采集和处理最新安全情报

## 未来扩展方向

1. **更多情报源支持**：扩展支持更多技术博客和社交媒体平台
2. **高级分析功能**：添加情报趋势分析、威胁预测等功能
3. **实时告警系统**：开发基于提取情报的实时安全告警机制
4. **交互式查询界面**：开发便于用户查询和分析情报的界面

## 总结

IntelliRadar是一个创新的开源情报收集与分析系统，它通过结合网页爬虫技术和大语言模型，实现了从情报源识别、内容采集到情报提取、验证和聚合的全流程自动化。系统不仅能够提高情报收集的效率，还能通过多源聚合提高情报的可靠性，为软件供应链安全提供强有力的支持。 