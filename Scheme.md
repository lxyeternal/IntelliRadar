# IntelliRadar

IntelliRadar is a project focused on collecting intelligence related to package managers from open-source data sources. The project focuses on gathering intelligence about malicious components in PyPI, NPM, Maven, and other package managers. IntelliRadar collects data from multiple intelligence sources, such as blogs, news websites, and social media. It utilizes "Least to Most" (LtM) prompting techniques in large language models (LLMs) to extract intelligence entities, analyze relationships between entities, and validate the information. Finally, IntelliRadar aggregates intelligence from different sources through a voting mechanism, providing more reliable and comprehensive package manager security intelligence.

## Workflow

The workflow of IntelliRadar is divided into the following key steps:

1. **Intelligence Source Identification**
   - Using keyword extraction and a snowball search engine method to identify intelligence sources.

2. **Web Text Collection**
   - Collecting web content related to package managers from multiple intelligence sources, including content from social media platforms such as Twitter and Reddit.

3. **Intelligence Entity Extraction**
   - Using the LtM prompting technique in LLMs to extract intelligence entities from the collected text content and further analyze the relationships between entities.

4. **Intelligence Aggregation**
   - Aggregating intelligence entities from different sources through a voting mechanism, parsing the generated JSON files, and outputting the processed intelligence data.

## Intelligence Sources

IntelliRadar's intelligence sources are divided into two categories: **unstructured sources** and **structured sources**.

### Unstructured Sources

These sources consist of blogs, news articles, and social media posts. The data from these sources is typically unstructured and requires web scraping and text processing tools for parsing. The primary unstructured sources include:

- **News Platforms and Security Companies**:  
  `Snyk`, `Qianxin`, `Datadoghq`, `JFrog`, `GitHub`, `Medium`, `Checkmarx`, `Sonatype`, `Bleeping Computer`, `Security Affairs`, `Fortinet`, `Phylum`, `ReversingLabs`, `Tuxcare`, `Cybersecurity News`, `RHISAC`, `Socket`, `Checkpoint`.

- **Social Media**:  
  `Twitter`, `Reddit`.

### Source Sankey Diagram

The Sankey diagram below illustrates the flow and categorization of the intelligence sources. The diagram highlights the relationship between structured and unstructured sources and how they contribute to the intelligence gathering process in the project.

![Sankey Diagram](/Users/blue/Documents/GitHub/SCC_Intelligence/Paper/images/sankey_source.png)

### Structured Sources

Structured sources are databases or repositories with well-defined data formats. These are easier to process and analyze due to their structured nature. The primary structured sources include:

- **Snyk Database**: Provides security vulnerability information on open-source software and dependencies.
- **OSV Database**: An open-source vulnerability database with publicly disclosed security information.
- **GitHub Advisory Database**: GitHub's repository of security advisories for open-source projects.

## Database Schema

The collected intelligence is stored in a structured database following this schema:

- **Package name**: The name of the affected package.
- **Package Manager**: The package manager the package belongs to (e.g., npm, PyPI).
- **Version**: The version of the affected package.
- **Date of discovery**: The date when the vulnerability or security issue was discovered.
- **Repository URL**: The URL of the repository related to the package.
- **Attack method**: Technical details on how the vulnerability or attack occurs.
- **Discoverer**: The individual or organization that discovered the issue.
- **List of affected systems**: A list of systems or components affected by the vulnerability.
- **Attack vector**: A description of how the vulnerability can be exploited by an attacker.
- **IOC (Indicators of compromise)**: Technical indicators such as IP addresses, URLs, file hashes, or specific strings that suggest the system may have been compromised.
- **Intelligence source**: The source of the intelligence (e.g., Snyk, GitHub Advisory).
- **Collected date**: The date when the intelligence data was collected.

## Conclusion

IntelliRadar combines multiple intelligence sources and leverages LLMs to extract and aggregate key intelligence. By integrating both structured and unstructured sources, IntelliRadar provides precise and comprehensive intelligence for package managers, helping users and maintainers make timely and informed security decisions.
