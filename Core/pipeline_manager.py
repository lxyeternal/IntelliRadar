#!/usr/bin/env python3
"""
IntelliRadar unified data processing pipeline manager.
Supports automatic processing of unstructured and structured data sources.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class PipelineManager:
    """Unified data processing pipeline manager."""

    def __init__(self, config_path: str = "Codes/pipeline_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        self._setup_paths()

        self.collection = None
        self.content_extractor = None
        self.llm_analyzer = None
        self.data_integrator = None


    def _load_collection(self):
        """Lazy-load WebPageCollection."""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'Collection'))
            from webpagecollection import WebPageCollection
            self.collection = WebPageCollection()
        except ImportError as e:
            self.logger.error(f"Failed to import WebPageCollection: {e}")
            raise


    def _load_content_extractor(self):
        """Lazy-load WebPageContent."""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'Collection'))
            from webpage_content import WebPageContent
            self.content_extractor = WebPageContent()
        except ImportError as e:
            self.logger.error(f"Failed to import WebPageContent: {e}")
            raise


    def _load_llm_analyzer(self):
        """Lazy-load LTMGPT."""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'GPTAnalysis'))
            from lst_gptuse import LTMGPT
            self.llm_analyzer = LTMGPT()
        except ImportError as e:
            self.logger.error(f"Failed to import LTMGPT: {e}")
            raise


    def _load_data_integrator(self):
        """Lazy-load DataIntegrity."""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'DataProcessing'))
            from DataIntegrity import DataIntegrity
            self.data_integrator = DataIntegrity()
        except ImportError as e:
            self.logger.error(f"Failed to import DataIntegrity: {e}")
            raise


    def _load_config(self) -> Dict:
        """Load configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Configuration file format error: {e}")


    def _setup_logging(self):
        """Set up logging."""
        log_dir = Path(self.config['paths']['logs_dir'])
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)


    def _setup_paths(self):
        """Create necessary directories."""
        for path_key, path_value in self.config['paths'].items():
            if path_key.endswith('_dir'):
                Path(path_value).mkdir(parents=True, exist_ok=True)


    def run_full_pipeline(self, source_types: List[str] = None):
        """Run the full pipeline.

        Args:
            source_types: Data source types to process ['unstructured', 'structured'].
                         If None, processes all types.
        """
        self.logger.info("Starting IntelliRadar data processing pipeline")
        start_time = time.time()

        if source_types is None:
            source_types = ['unstructured', 'structured']

        try:
            if 'unstructured' in source_types:
                self.logger.info("Processing unstructured data sources...")
                self._process_unstructured_sources()

            if 'structured' in source_types:
                self.logger.info("Processing structured data sources...")
                self._process_structured_sources()

            self.logger.info("Starting data aggregation...")
            self._aggregate_all_data()

            if self.config['pipeline_settings']['update_frontend']:
                self.logger.info("Updating frontend data...")
                self._update_frontend()

            elapsed_time = time.time() - start_time
            self.logger.info(f"Pipeline completed, total time: {elapsed_time:.2f}s")

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            raise


    def _process_unstructured_sources(self):
        """Process unstructured data sources."""
        unstructured_config = self.config['data_sources']['unstructured']

        for source_info in unstructured_config['sources']:
            if not source_info['enabled']:
                continue

            source_name = source_info['name']
            method_name = source_info['collection_method']

            self.logger.info(f"Processing data source: {source_name}")

            try:
                self._collect_source_links(source_name, method_name)
                self._extract_source_content(source_name)

                if source_info['requires_llm']:
                    self._analyze_with_llm(source_name)

            except Exception as e:
                self.logger.error(f"Error processing data source {source_name}: {str(e)}")
                continue


    def _process_structured_sources(self):
        """Process structured data sources."""
        structured_config = self.config['data_sources']['structured']

        for source_info in structured_config['sources']:
            if not source_info['enabled']:
                continue

            source_name = source_info['name']
            method_name = source_info['collection_method']

            self.logger.info(f"Processing structured data source: {source_name}")

            try:
                self._fetch_structured_data(source_name, method_name, source_info)

            except Exception as e:
                self.logger.error(f"Error processing structured data source {source_name}: {str(e)}")
                continue


    def _collect_source_links(self, source_name: str, method_name: str):
        """Collect links for a given data source."""
        self.logger.info(f"  Collecting links for {source_name}...")

        if self.collection is None:
            self._load_collection()

        if hasattr(self.collection, method_name):
            method = getattr(self.collection, method_name)
            method()
            self.logger.info(f"  Link collection complete for {source_name}")
        else:
            self.logger.warning(f"  Method not found: {method_name}")


    def _extract_source_content(self, source_name: str):
        """Extract content for a given data source."""
        self.logger.info(f"  Extracting content for {source_name}...")

        waiting_file = Path(self.config['paths']['waiting_collection'])
        if not waiting_file.exists():
            self.logger.warning(f"  Waiting file not found: {waiting_file}")
            return

        if self.content_extractor is None:
            self._load_content_extractor()

        self.logger.info(f"  Content extraction requires WebPageContent interface implementation")
        return 0


    def _analyze_with_llm(self, source_name: str):
        """Analyze a data source using LLM."""
        self.logger.info(f"  LLM analysis for {source_name}...")

        content_dir = Path(self.config['paths']['content_dir']) / source_name
        if not content_dir.exists():
            self.logger.warning(f"  Content directory does not exist: {content_dir}")
            return

        if self.llm_analyzer is None:
            self._load_llm_analyzer()

        self.logger.info(f"  LLM analysis requires LTMGPT interface implementation")

        steps = ['extract', 'relation', 'verify']
        for step in steps:
            self.logger.info(f"    Executing {step} step...")

            try:
                # self.llm_analyzer.some_method(source_name, step)
                self.logger.info(f"    {step} step complete")

            except Exception as e:
                self.logger.error(f"    {step} step failed: {str(e)}")
                continue


    def _fetch_structured_data(self, source_name: str, method_name: str, source_info: Dict):
        """Fetch structured data from a given source."""
        self.logger.info(f"  Fetching structured data for {source_name}...")

        if source_name == 'osv':
            self._fetch_osv_data()
        elif source_name == 'github_advisory':
            self._fetch_github_advisory_data()
        elif source_name == 'snyk_vulndb':
            self._fetch_snyk_vulndb_data()
        else:
            self.logger.warning(f"  Unimplemented structured data source: {source_name}")


    def _fetch_osv_data(self):
        """Fetch OSV data."""
        # TODO: Implement OSV API calls
        self.logger.info("    Fetching OSV vulnerability data...")
        pass


    def _fetch_github_advisory_data(self):
        """Fetch GitHub Advisory data."""
        # TODO: Implement GitHub Advisory API calls
        self.logger.info("    Fetching GitHub Advisory data...")
        pass


    def _fetch_snyk_vulndb_data(self):
        """Fetch Snyk vulnerability database data."""
        # TODO: Implement Snyk VulnDB API calls
        self.logger.info("    Fetching Snyk vulnerability database data...")
        pass


    def _aggregate_all_data(self):
        """Aggregate all data sources."""
        self.logger.info("Starting data aggregation...")

        try:
            if self.data_integrator is None:
                self._load_data_integrator()

            # self.data_integrator.integrate_all_sources()
            self.logger.info("  Data aggregation requires DataIntegrity interface implementation")
            self.logger.info("Data aggregation complete")

        except Exception as e:
            self.logger.error(f"Data aggregation failed: {str(e)}")
            raise


    def _update_frontend(self):
        """Update frontend data."""
        self.logger.info("Updating frontend data...")

        try:
            import subprocess
            result = subprocess.run([
                sys.executable,
                'Codes/update_frontend_data.py'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info("Frontend data update complete")
            else:
                self.logger.error(f"Frontend data update failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"Frontend data update error: {str(e)}")


    def run_single_source(self, source_name: str, source_type: str = 'unstructured'):
        """Run processing for a single data source.

        Args:
            source_name: Name of the data source.
            source_type: Source type ('unstructured' or 'structured').
        """
        self.logger.info(f"Processing single data source: {source_name} ({source_type})")

        try:
            if source_type == 'unstructured':
                sources = self.config['data_sources']['unstructured']['sources']
                source_info = next((s for s in sources if s['name'] == source_name), None)

                if not source_info:
                    raise ValueError(f"Data source configuration not found: {source_name}")

                if not source_info['enabled']:
                    self.logger.warning(f"Data source {source_name} is not enabled")
                    return

                method_name = source_info['collection_method']

                self._collect_source_links(source_name, method_name)
                self._extract_source_content(source_name)

                if source_info['requires_llm']:
                    self._analyze_with_llm(source_name)

            elif source_type == 'structured':
                sources = self.config['data_sources']['structured']['sources']
                source_info = next((s for s in sources if s['name'] == source_name), None)

                if not source_info:
                    raise ValueError(f"Data source configuration not found: {source_name}")

                if not source_info['enabled']:
                    self.logger.warning(f"Data source {source_name} is not enabled")
                    return

                method_name = source_info['collection_method']
                self._fetch_structured_data(source_name, method_name, source_info)

            self.logger.info(f"Data source {source_name} processing complete")

        except Exception as e:
            self.logger.error(f"Error processing data source {source_name}: {str(e)}")
            raise


    def get_pipeline_status(self) -> Dict:
        """Get pipeline status."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'statistics': {}
        }

        for source_type in ['unstructured', 'structured']:
            sources = self.config['data_sources'][source_type]['sources']
            for source_info in sources:
                source_name = source_info['name']
                status['sources'][source_name] = {
                    'type': source_type,
                    'enabled': source_info['enabled'],
                    'requires_llm': source_info.get('requires_llm', False),
                    'last_processed': self._get_last_processed_time(source_name)
                }

        status['statistics'] = {
            'total_content_files': self._count_content_files(),
            'total_llm_outputs': self._count_llm_outputs(),
            'csv_size': self._get_csv_size()
        }

        return status


    def _get_last_processed_time(self, source_name: str) -> Optional[str]:
        """Get the last processing time for a data source."""
        content_dir = Path(self.config['paths']['content_dir']) / source_name
        if not content_dir.exists():
            return None

        files = list(content_dir.glob('*.txt'))
        if not files:
            return None

        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        return datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()


    def _count_content_files(self) -> int:
        """Count content files."""
        content_dir = Path(self.config['paths']['content_dir'])
        return len(list(content_dir.rglob('*.txt')))


    def _count_llm_outputs(self) -> int:
        """Count LLM output files."""
        llm_dir = Path(self.config['paths']['llm_output_dir'])
        return len(list(llm_dir.rglob('*.json')))


    def _get_csv_size(self) -> int:
        """Get CSV file size."""
        csv_file = Path(self.config['paths']['csv_output'])
        return csv_file.stat().st_size if csv_file.exists() else 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='IntelliRadar data processing pipeline')
    parser.add_argument('--config', default='Codes/pipeline_config.json', help='Configuration file path')
    parser.add_argument('--source', help='Process a single data source')
    parser.add_argument('--type', choices=['unstructured', 'structured'], help='Data source type')
    parser.add_argument('--status', action='store_true', help='Show pipeline status')
    parser.add_argument('--sources', nargs='+', choices=['unstructured', 'structured'],
                       help='Data source types to process')

    args = parser.parse_args()

    manager = PipelineManager(args.config)

    if args.status:
        status = manager.get_pipeline_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))

    elif args.source:
        source_type = args.type or 'unstructured'
        manager.run_single_source(args.source, source_type)

    else:
        manager.run_full_pipeline(args.sources)
