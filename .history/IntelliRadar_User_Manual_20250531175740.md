# IntelliRadar User Manual

## Introduction

IntelliRadar is an intelligent intelligence collection and analysis system focused on gathering package manager security-related intelligence from open-source data sources. This manual will guide you through the setup, configuration, and operation of the system.

## System Requirements

- Python 3.8 or higher
- Chrome browser (for Selenium)
- 16GB RAM recommended
- Stable internet connection
- OpenAI API key for LLM functionality

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/IntelliRadar.git
   cd IntelliRadar
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up configuration:
   - Open `Configs/config.json`
   - Add your OpenAI API key
   - Configure intelligence sources as needed

## System Structure

IntelliRadar consists of five main modules:

1. **IntelliSource**: Identifies and manages intelligence sources
2. **Collection**: Collects web links and content from sources
3. **GPTAnalysis**: Extracts intelligence entities using LLM
4. **Aggregate**: Integrates and validates intelligence from different sources
5. **Keywords**: Processes keywords for source identification

## Basic Operation

### Starting the System

To start the complete intelligence collection pipeline:

```
python Codes/main.py --full-pipeline
```

For individual module execution:

```
python Codes/main.py --module [module_name]
```

Available module options: `source`, `collection`, `analysis`, `aggregate`

### Configuration Options

Edit `Configs/config.json` to customize:

- Intelligence sources
- Crawling parameters
- LLM model selection
- Output formats

## Module-Specific Operations

### 1. Intelligence Source Identification

To identify new intelligence sources:

```
python Codes/main.py --module source --keyword-file keywords.txt
```

The system will search for potential intelligence sources based on the keywords in the specified file.

### 2. Web Page Collection

To collect links from configured sources:

```
python Codes/main.py --module collection --source all
```

To collect from specific sources:

```
python Codes/main.py --module collection --source snyk,github
```

The collected links will be stored in the waiting collection file.

### 3. Content Extraction

To extract content from collected links:

```
python Codes/main.py --module collection --extract-content
```

The extracted content will be saved to `Dataset/Content/{source}/{timestamp}.txt`.

### 4. Intelligence Analysis

To analyze extracted content using LLM:

```
python Codes/main.py --module analysis --model gpt-4o
```

Available model options: `gpt-4o`, `gpt-3.5-turbo`

The analysis results will be saved as JSON files in `Dataset/Json/{source}/`.

### 5. Intelligence Aggregation

To aggregate and validate intelligence from all sources:

```
python Codes/main.py --module aggregate --output csv
```

The aggregated intelligence will be saved as CSV files in `Dataset/CSV/`.

## Data Flow Management

### Input Files

- `Keywords/keywords.txt`: Contains keywords for source identification
- `waiting_collection.txt`: Contains links waiting to be processed
- `collected_pagelinks.txt`: Contains already processed links

### Output Files

- `Dataset/Content/{source}/{timestamp}.txt`: Extracted content
- `Dataset/Json/{source}/{timestamp}_verify_{model}.json`: Analysis results
- `Dataset/CSV/intelligence_{date}.csv`: Aggregated intelligence

## Advanced Usage

### Adding New Intelligence Sources

1. Identify the source URL pattern
2. Add a new method in `WebPageCollection` class for the source
3. Add a corresponding content extraction method in `WebPageContent` class
4. Update the source list in `config.json`

Example for adding a new blog source:

```python
def new_blog_source(self):
    # Source-specific collection logic
    pageurl = "https://example.com/security-blog"
    self.driver.get(pageurl)
    # Extract links and save
```

### Customizing LLM Prompts

To customize the prompts used for intelligence extraction:

1. Navigate to `Codes/GPTAnalysis/LtM_prompts/`
2. Edit the prompt templates for entity extraction, relation analysis, or verification
3. Update the prompt type in the code or config file

### Batch Processing

For processing large datasets:

```
python Codes/main.py --batch-size 50 --module analysis
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Check internet connection
   - Verify proxy settings in `config.json`
   - Increase request timeout values

2. **LLM API Errors**
   - Verify API key is correct
   - Check API rate limits
   - Try reducing batch size

3. **Content Extraction Issues**
   - Update Selenium and Chrome drivers
   - Check source-specific extraction logic
   - Review HTML structure changes in the source

### Logs

System logs are available in the `Logs/` directory:
- `collection.log`: Web collection logs
- `analysis.log`: LLM analysis logs
- `error.log`: Error messages

## Maintenance

### Regular Updates

1. Update intelligence sources list quarterly
2. Check for HTML structure changes in monitored sites
3. Update LLM prompts to improve extraction accuracy

### Data Management

1. Archive processed content monthly
2. Back up intelligence CSV files
3. Clean up temporary files using:
   ```
   python Codes/main.py --cleanup
   ```

## Performance Optimization

- Use `--threads` parameter to specify the number of concurrent processes
- Set `--cache` to enable caching of LLM responses
- Use `--limit` to restrict the number of sources processed in a single run

## Contact & Support

For issues, feature requests, or contributions, please:
- Submit an issue on GitHub
- Contact the development team at support@intelliradar.com

---

© 2024 IntelliRadar Project. All rights reserved. 