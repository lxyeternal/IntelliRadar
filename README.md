# IntelliRadar

A comprehensive platform for pinpointing malicious package information from cyber intelligence. IntelliRadar automates the collection, extraction, and aggregation of threat intelligence from 20+ security blogs, social media, and vulnerability databases to detect malicious packages in PyPI and npm ecosystems.

> Accepted at **ICSE 2026**

## Architecture

IntelliRadar follows a multi-stage pipeline where each module operates independently:

```
Keywords → SourceDiscovery → Collection → Analysis → Aggregation
```

1. **Keywords** - Extract common keywords (LDA) and special keywords (TF-IDF) from known malicious package reports
2. **SourceDiscovery** - Use keywords to discover intelligence sources via Google search and URL analysis
3. **Collection** - Scrape content from security blogs, Reddit, OSV, Snyk, and other sources
4. **Analysis** - Extract structured intelligence using LLM with 3-step Chain-of-Thought (Entity Extraction → Relationship Analysis → Information Verification)
5. **Aggregation** - Resolve conflicts across sources using a multi-source voting mechanism

Additional modules:
- **Verification** - Cross-validate extracted data against Snyk, OSV, GitHub Advisory, and npm registry
- **Downstream** - Scan package mirrors for malicious package propagation

## Project Structure

```
IntelliRadar/
├── Core/                        # Main codebase
│   ├── Keywords/                # Keyword extraction (LDA, TF-IDF)
│   ├── SourceDiscovery/         # Source identification via search engines
│   ├── Collection/              # Web scraping and content extraction
│   ├── Analysis/                # LLM-based intelligence extraction
│   ├── Aggregation/             # Multi-source voting and data export
│   ├── Verification/            # Cross-validation with vulnerability DBs
│   ├── Downstream/              # Mirror scanning
│   ├── pipeline.py              # Pipeline orchestrator
│   └── pipeline_manager.py      # Config-driven pipeline manager
├── Configs/                     # Configuration files
├── Dataset/                     # Data storage (content, JSON, CSV)
├── Experiment/                  # Experimental scripts
└── Case/                        # Case studies
```

## Maliverse Platform

Browse the collected malicious package data at: [maliverse.org](https://www.maliverse.org/)

## Citation

If you use IntelliRadar in your research, please cite our paper:

```bibtex
@misc{guo2025intelliradarcomprehensiveplatformpinpoint,
      title={IntelliRadar: A Comprehensive Platform to Pinpoint Malicious Package Information from Cyber Intelligence},
      author={Wenbo Guo and Chengwei Liu and Limin Wang and Yiran Zhang and Jiahui Wu and Zhengzi Xu and Yang Liu},
      year={2025},
      eprint={2409.15049},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2409.15049},
}
```

## License

This project is for research purposes. Please refer to the LICENSE file for details.
