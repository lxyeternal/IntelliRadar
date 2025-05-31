# IntelliRadar Project Detailed Analysis

## Project Overview

IntelliRadar is an intelligent intelligence collection and analysis system focused on gathering package manager security-related intelligence from open-source data sources. The project employs a systematic process to collect information from multiple intelligence sources (such as security blogs, technical websites, social media, etc.), utilizing Large Language Models (LLM) with "Chain of Thought (CoT)" prompting techniques to extract intelligence entities, analyze entity relationships, and aggregate intelligence from different sources through a voting mechanism, ultimately providing more reliable and comprehensive intelligence data.

## Core Features

- **Multi-source Intelligence Collection**: Automatically gather package manager security-related articles and discussions from multiple technical blogs and social media platforms
- **Intelligent Intelligence Extraction**: Use LLM technology to intelligently identify and extract intelligence entities and relationships from text
- **Data Integration and Verification**: Verify and integrate extracted intelligence to improve reliability
- **Structured Data Output**: Output processed intelligence in structured formats (such as CSV) for subsequent applications

## System Architecture

### Overall Architecture

IntelliRadar adopts a modular system architecture, mainly including the following core modules:

1. **Intelligence Source Identification Module**: Identify and manage intelligence sources
2. **Web Collection Module**: Crawl content from intelligence sources
3. **Content Extraction Module**: Extract text content from web pages
4. **Intelligence Analysis Module**: Use LLM technology to extract intelligence entities and relationships from text
5. **Intelligence Aggregation Module**: Integrate and verify intelligence from different sources

### Data Flow

The data flow in the system is as follows:

```
Intelligence Sources (Blogs/Social Media) → Web Link Collection → Web Content Extraction → LLM Intelligence Entity Extraction → Intelligence Aggregation and Verification → Structured Data Output
```

## Detailed Implementation Process

### 1. Intelligence Source Identification and Management

The project uses the `IntelliSource` module with keyword searches and snowball methods to identify information sources:

- **Keyword Extraction**: Use custom keyword lists to search for potential intelligence sources
- **Source Management**: The system can track and manage multiple intelligence sources, including technical blogs (such as Snyk, JFrog, etc.) and social media platforms (such as Reddit, Twitter)

### 2. Web Link Collection

The `WebPageCollection` class in the `Collection` module is responsible for collecting historical and latest article links from various intelligence sources:

- **Support for Multiple Website Structures**: Customize collection methods for different blog platforms (such as `snyk_blog`, `github_blog`, etc.)
- **Incremental Collection**: Record processed links to avoid duplicate collection
- **Link Storage**: Store links to be collected in `waiting_collection.txt` and collected links in `collected_pagelinks.txt`

Code example:
```python
def bleepingcomputer_blog(self):
    for page_index in range(1, 3):
        if page_index == 1:
            pageurl = "https://www.bleepingcomputer.com/tag/pypi/"
        else:
            pageurl = self.bleepingcomputer.format(page_index)
        self.driver.get(pageurl)
        # Extract links and dates from the web page
        # ...
        if li_url not in self.old_webpage_dict.get("bleepingcomputer_oss", []):
            self.write_txt("bleepingcomputer_oss", formatted_date, li_url)
```

### 3. Web Content Extraction

The `WebPageContent` class is responsible for extracting text content from collected links:

- **Targeted Extraction**: Customize content extraction methods for each intelligence source (such as `medium_content`, `snyk_content`, etc.)
- **Multi-element Parsing**: Process different types of HTML elements, such as tables, lists, code blocks, etc.
- **Content Storage**: Save extracted content to `Dataset/Content/{source}/{timestamp}.txt` files

Code example:
```python
def snyk_content(self, timestamp, url):
    try:
        driver = webdriver.Chrome(service=self.service, options=self.options)
        driver.get(url)
        # Wait for page loading and extract content elements
        # ...
        page_content = self.parse_elements(driver, article, timestamp)
        content_file = os.path.join(self.text_dir, "snyk", f"{timestamp}.txt")
        self.write_text(page_content, content_file)
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
```

### 4. Intelligence Entity Extraction

The `LTMGPT` class in the `GPTAnalysis` module uses large language models for intelligence entity extraction:

- **Chain of Thought (CoT) Prompting**: Adopt a step-by-step approach to guide LLM in intelligence extraction
- **Three-step Analysis Process**:
  1. **Entity Extraction**: Identify key intelligence entities from text (such as package names, attack methods, etc.)
  2. **Relationship Analysis**: Analyze relationships between entities (such as which package uses what attack method)
  3. **Information Verification**: Verify the accuracy and completeness of extracted information
- **Result Serialization**: Save extraction results in JSON format

Code example:
```python
def process_content(self, source, content_file_path, content_file_name):
    # Read text content
    content = self.read_txt(content_file_path)
    
    # Use LLM for three-step analysis
    model = "gpt-4o"
    prompt_type = "cot"  # Chain of Thought
    
    # 1. Extract entities
    extract_prompt = self.get_prompt("extract", prompt_type)
    extracted_entity = self.entity_extract_llm(content, [], model, extract_prompt)
    
    # 2. Analyze relationships
    relation_prompt = self.get_prompt("relation", prompt_type)
    entity_relation = self.entity_realtion_llm(content, extracted_entity, model, relation_prompt)
    
    # 3. Verify information
    verify_prompt = self.get_prompt("verify", prompt_type)
    verified_info = self.info_verify_llm(content, entity_relation, model, verify_prompt)
    
    # Save results
    timestamp = content_file_name.split('.')[0]
    json_file_path = os.path.join(self.json_dir, source, f"{timestamp}_verify_gpt4.json")
    self.save_json(verified_info, json_file_path)
```

### 5. Intelligence Aggregation and Verification

The `DataIntegrity` class in the `Aggregate` module is responsible for processing and aggregating extracted intelligence:

- **JSON Parsing**: Parse LLM-generated JSON format intelligence
- **Data Standardization**: Process data in different formats and unify them into a standard format
- **CSV Output**: Save processed intelligence as CSV format for subsequent analysis and applications

Code example:
```python
def parse_json_file(self, file_path):
    data_timestamp = self.parse_timestamp(file_path)
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
        file_content = self.remove_json_comments(file_content)
        data = json.loads(file_content)
        
        # Parse and process JSON data
        parsed_data = []
        for item in data:
            # Process fields such as package name, attack method, etc.
            # ...
            parsed_entry = {
                "Package Name": package_name,
                "Package Manager": item.get("Package Manager", ""),
                # Other fields...
                "Source": self.intellisource
            }
            parsed_data.append(parsed_entry)
        return parsed_data
```

## Process Example Analysis

The following is a complete process example of IntelliRadar processing an intelligence source article:

1. **Link Collection**: The system collects an article link about package manager security from the Snyk blog
2. **Content Extraction**: The system extracts the article content from the link and saves it as `snyk_88.txt`
3. **Intelligence Analysis**: LLM analyzes the article content and identifies intelligence entities involved, such as package names (notevil, argencoders-notevil, and libxmljs), attack methods (Prototype Pollution and Type Confusion), etc.
4. **Relationship Establishment**: Determine relationships between entities, such as the notevil package having a Prototype Pollution vulnerability with CVE number CVE-2021-23771
5. **Data Integration**: The system saves the analysis results as a JSON file `snyk_88_gpt4.json`
6. **Format Conversion**: Finally, convert the results to CSV format, containing standard fields such as package name, package manager, version, etc.

## File Structure

The main file structure of the project is as follows:

```
├── Codes
│   ├── Aggregate          # Intelligence aggregation and verification module
│   │   ├── dataintegrity.py  # JSON parsing and CSV output
│   │   └── intellivote.py    # Intelligence aggregation voting mechanism
│   ├── Collection         # Web collection module
│   │   ├── webpage_collection.py  # Link collection
│   │   └── webpage_content.py     # Content extraction
│   ├── GPTAnalysis        # Intelligence analysis module
│   │   ├── lst-gptuse.py         # LLM intelligence extraction
│   │   └── LtM_prompts/          # Prompt engineering templates
│   ├── IntelliSource      # Intelligence source identification module
│   │   ├── google_search.py      # Search engine collection
│   │   └── googleurl_analysis.py # URL analysis
│   ├── Keywords           # Keyword processing module
│   └── main.py            # Main program entry
├── Configs
│   └── config.json        # Configuration file
└── Dataset                # Data storage
    ├── Content            # Extracted web content
    ├── Json               # LLM analysis JSON results
    └── CSV                # Final CSV format intelligence
```

## Key Technology Analysis

### 1. Chain of Thought (CoT) Prompting

IntelliRadar uses Chain of Thought (CoT) prompting techniques to guide LLM in intelligence analysis:

- **Step Decomposition**: Break down complex tasks into multiple simple steps
- **Progressive Analysis**: Gradually deepen from simple entity recognition to complex relationship analysis
- **Result Verification**: Guide LLM to self-verify results through specific prompts

### 2. Web Crawling Technology and Anti-crawling Strategies

The system employs various technologies to achieve stable web collection:

- **Selenium+BeautifulSoup Combination**: Use Selenium to handle dynamically loaded content and BeautifulSoup to parse HTML
- **Anti-crawling Bypass**: Simulate real browser behavior to avoid being identified as a crawler by target websites
- **Incremental Collection**: Record collected links to avoid repeated processing

### 3. Intelligence Entity Aggregation

Improve intelligence reliability by integrating information from multiple intelligence sources:

- **Consistency Verification**: Compare the same entity information from different sources
- **Complementary Completion**: Different sources may provide complementary information, and the system can integrate this information
- **Structured Output**: Standardized output format facilitates subsequent analysis and applications

## Application Scenarios

The IntelliRadar system can be applied to multiple security-related scenarios:

1. **Software Supply Chain Security Monitoring**: Timely discover and respond to security threats in package managers
2. **Vulnerability Intelligence Collection**: Automatically collect vulnerability information for open-source components
3. **Security Research and Analysis**: Provide structured intelligence data for security researchers
4. **Risk Assessment**: Assess potential security risks in software dependencies

## System Advantages

1. **High Degree of Automation**: Full-process automation from intelligence source identification to intelligence aggregation
2. **Strong Adaptability**: Easily expand support for new intelligence sources and data formats
3. **High Intelligence Quality**: Improve intelligence accuracy through LLM and multi-source aggregation
4. **Good Real-time Performance**: Collect and process the latest security intelligence in a timely manner

## Future Expansion Directions

1. **More Intelligence Source Support**: Expand support for more technical blogs and social media platforms
2. **Advanced Analysis Functions**: Add intelligence trend analysis, threat prediction, and other functions
3. **Real-time Alert System**: Develop a real-time security alert mechanism based on extracted intelligence
4. **Interactive Query Interface**: Develop an interface for users to query and analyze intelligence

## Summary

IntelliRadar is an innovative open-source intelligence collection and analysis system that achieves full-process automation from intelligence source identification, content collection to intelligence extraction, verification, and aggregation by combining web crawler technology and large language models. The system not only improves the efficiency of intelligence collection but also enhances the reliability of intelligence through multi-source aggregation, providing strong support for software supply chain security. 