#!/usr/bin/env python3
"""
Frontend data exporter.
Converts processed threat intelligence data into frontend-compatible formats.
"""

import json
import logging
import pandas as pd
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class FrontendDataUpdater:
    """Exports and updates frontend data from CSV threat intelligence records."""

    def __init__(self, config_path: str = "Codes/pipeline_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        self.csv_file = Path(self.config['paths']['csv_output'])
        self.frontend_dir = Path(self.config['paths']['frontend_dir'])

        self.packages_json = self.frontend_dir / "aggregated_packages.json"
        self.stats_json = self.frontend_dir / "Intelliradar_data.json"


    def _load_config(self) -> Dict:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'paths': {
                    'csv_output': 'Dataset/CSV/integrity.csv',
                    'frontend_dir': 'frontend/'
                }
            }


    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)


    def update_all_frontend_data(self):
        """Update all frontend data files."""
        self.logger.info("Starting frontend data update...")

        try:
            if not self.csv_file.exists():
                self.logger.error(f"CSV file not found: {self.csv_file}")
                return False

            self.logger.info("Reading CSV data...")
            df = pd.read_csv(self.csv_file)
            self.logger.info(f"Successfully read {len(df)} records")

            self.frontend_dir.mkdir(exist_ok=True)

            self.logger.info("Generating package detail data...")
            self._update_packages_data(df)

            self.logger.info("Generating statistics data...")
            self._update_statistics_data(df)

            self.logger.info("Frontend data update complete")
            return True

        except Exception as e:
            self.logger.error(f"Frontend data update failed: {str(e)}")
            return False


    def _update_packages_data(self, df: pd.DataFrame):
        """Generate package detail JSON from CSV data."""
        packages_data = []

        for _, row in df.iterrows():
            try:
                package_info = {
                    "packageName": self._clean_string(row.get('Package Name', '')),
                    "packageManager": self._clean_string(row.get('Package Manager', '')),
                    "version": self._parse_version(row.get('Version', '')),
                    "discoveryDate": self._parse_date(row.get('Discovery Date', '')),
                    "repositoryUrl": self._clean_string(row.get('Repository URL', '')),
                    "attackMethod": self._clean_string(row.get('Attack Method', '')),
                    "discoverer": self._clean_string(row.get('Discoverer', '')),
                    "impactedSystems": self._clean_string(row.get('Impacted Systems', '')),
                    "attackVector": self._clean_string(row.get('Attack Vector', '')),
                    "indicatorsOfCompromise": self._clean_string(row.get('Indicators of Compromise', '')),
                    "timestamp": self._parse_date(row.get('Timestamp', '')),
                    "source": self._clean_string(row.get('Source', ''))
                }

                if package_info["packageName"]:
                    packages_data.append(package_info)

            except Exception as e:
                self.logger.warning(f"Error processing record: {str(e)}")
                continue

        with open(self.packages_json, 'w', encoding='utf-8') as f:
            json.dump(packages_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Generated package detail data: {len(packages_data)} packages")


    def _update_statistics_data(self, df: pd.DataFrame):
        """Generate statistics JSON from CSV data."""
        try:
            total_packages = len(df)
            total_sources = df['Source'].nunique() if 'Source' in df.columns else 0

            package_manager_stats = {}
            if 'Package Manager' in df.columns:
                pm_counts = df['Package Manager'].value_counts()
                package_manager_stats = pm_counts.to_dict()

            source_stats = {}
            if 'Source' in df.columns:
                source_counts = df['Source'].value_counts()
                source_stats = source_counts.to_dict()

            # Count discoveries in the last 30 days
            recent_discoveries = 0
            if 'Discovery Date' in df.columns:
                df_copy = df.copy()
                df_copy['Discovery Date'] = pd.to_datetime(df_copy['Discovery Date'], errors='coerce')
                recent_date = pd.Timestamp.now() - pd.Timedelta(days=30)
                recent_discoveries = len(df_copy[df_copy['Discovery Date'] > recent_date])

            stats_data = {
                "lastUpdated": datetime.now().isoformat(),
                "totalPackages": total_packages,
                "totalSources": total_sources,
                "recentDiscoveries": recent_discoveries,
                "packageManagerStats": package_manager_stats,
                "sourceStats": source_stats,
                "topPackageManagers": self._get_top_items(package_manager_stats, 5),
                "topSources": self._get_top_items(source_stats, 5),
                "metadata": {
                    "dataVersion": "1.0",
                    "generatedBy": "IntelliRadar Pipeline",
                    "description": "Threat intelligence statistics"
                }
            }

            with open(self.stats_json, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Generated statistics: {total_packages} packages, {total_sources} sources")

        except Exception as e:
            self.logger.error(f"Failed to generate statistics: {str(e)}")


    def _clean_string(self, value: Any) -> str:
        """Clean and normalize a string value, including list-formatted strings."""
        if pd.isna(value):
            return ""

        str_value = str(value)

        # Handle list-formatted strings like "['item1', 'item2']"
        if str_value.startswith('[') and str_value.endswith(']'):
            try:
                import ast
                parsed_list = ast.literal_eval(str_value)
                if isinstance(parsed_list, list):
                    return ", ".join(str(item) for item in parsed_list)
            except:
                pass

        return str_value.strip()


    def _parse_version(self, value: Any) -> str:
        """Parse version info, extracting first version from list format."""
        cleaned = self._clean_string(value)

        if cleaned.startswith('[') and cleaned.endswith(']'):
            try:
                import ast
                parsed_list = ast.literal_eval(cleaned)
                if isinstance(parsed_list, list) and parsed_list:
                    return str(parsed_list[0])
            except:
                pass

        return cleaned


    def _parse_date(self, value: Any) -> str:
        """Parse and normalize a date value to YYYY-MM-DD format."""
        if pd.isna(value):
            return ""

        try:
            parsed_date = pd.to_datetime(value)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return str(value).strip()


    def _get_top_items(self, stats_dict: Dict, top_n: int) -> List[Dict]:
        """Return the top N items from a stats dictionary sorted by count."""
        if not stats_dict:
            return []

        sorted_items = sorted(stats_dict.items(), key=lambda x: x[1], reverse=True)
        return [
            {"name": name, "count": count}
            for name, count in sorted_items[:top_n]
        ]


    def get_update_status(self) -> Dict:
        """Return current status of all data files."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "csv_file": {
                "exists": self.csv_file.exists(),
                "size": self.csv_file.stat().st_size if self.csv_file.exists() else 0,
                "modified": datetime.fromtimestamp(self.csv_file.stat().st_mtime).isoformat() if self.csv_file.exists() else None
            },
            "packages_json": {
                "exists": self.packages_json.exists(),
                "size": self.packages_json.stat().st_size if self.packages_json.exists() else 0,
                "modified": datetime.fromtimestamp(self.packages_json.stat().st_mtime).isoformat() if self.packages_json.exists() else None
            },
            "stats_json": {
                "exists": self.stats_json.exists(),
                "size": self.stats_json.stat().st_size if self.stats_json.exists() else 0,
                "modified": datetime.fromtimestamp(self.stats_json.stat().st_mtime).isoformat() if self.stats_json.exists() else None
            }
        }

        return status


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Update frontend data')
    parser.add_argument('--config', default='Codes/pipeline_config.json', help='Config file path')
    parser.add_argument('--status', action='store_true', help='Show update status')

    args = parser.parse_args()

    updater = FrontendDataUpdater(args.config)

    if args.status:
        status = updater.get_update_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        success = updater.update_all_frontend_data()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
