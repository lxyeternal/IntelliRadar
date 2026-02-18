import json
from typing import List, Dict, Any, Set
from datetime import datetime


class MaliciousPackageAggregator:

    def __init__(self):
        self.string_fields = {
            'Package Name',
            'Package Manager'
        }

        self.voting_fields = {
            'Method of Attack',
            'Attack Vector',
            'Discoverer',
            'Impacted Systems',
            'Date of Discovery'
        }

        self.merge_fields = {
            'Indicators of Compromise',
            'Source',
            'source_link'
        }


    def _value_to_string(self, value: Any) -> str:
        if isinstance(value, list):
            return ','.join(sorted(str(x) for x in value))
        return str(value)


    def _string_to_original(self, string_value: str, original_values: List[Any]) -> Any:
        """Find matching value in original values."""
        for value in original_values:
            if self._value_to_string(value) == string_value:
                return value
        return string_value


    def aggregate_packages(self, input_file: str, output_file: str):
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        grouped_data = self._group_by_manager_and_name(data)

        aggregated_results = []
        for package_manager, packages in grouped_data.items():
            for package_name, package_data in packages.items():
                aggregated_package = self._aggregate_single_package(
                    package_data,
                    package_manager,
                    package_name
                )
                aggregated_results.append(aggregated_package)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated_results, f, indent=2, ensure_ascii=False)

        return aggregated_results


    def _group_by_manager_and_name(self, data: List[Dict]) -> Dict:
        """Group data by package manager and package name."""
        grouped = {}
        for item in data:
            manager = item.get('Package Manager')
            name = item.get('Package Name')
            if not manager or not name:
                continue

            if manager not in grouped:
                grouped[manager] = {}
            if name not in grouped[manager]:
                grouped[manager][name] = []

            grouped[manager][name].append(item)

        return grouped


    def _aggregate_single_package(
            self,
            package_data: List[Dict],
            package_manager: str,
            package_name: str
    ) -> Dict:
        """Aggregate all data for a single package."""
        result = {
            'Package Name': package_name,
            'Package Manager': package_manager
        }

        all_fields = set()
        for item in package_data:
            all_fields.update(item.keys())

        for field in all_fields:
            if field in result:
                continue

            if field in self.voting_fields:
                result[field] = self._vote_field(package_data, field)
            else:
                result[field] = self._merge_field(package_data, field)

        return result


    def _is_list_field(self, field: str, values: List[Any]) -> bool:
        """Determine if a field should be treated as a list type."""
        if field in self.string_fields:
            return False
        return any(isinstance(v, list) for v in values if v is not None)


    def _vote_field(self, package_data: List[Dict], field: str) -> Any:
        """Vote among conflicting field values, breaking ties by latest date."""
        values = []
        original_values = []
        for item in package_data:
            value = item.get(field)
            if value is not None:
                values.append((self._value_to_string(value), item.get('post_date', '')))
                original_values.append(value)

        if not values:
            return None

        if len(values) == 1:
            return original_values[0]

        # Count occurrences and track latest date per value
        value_counts = {}
        value_dates = {}
        for str_value, date in values:
            value_counts[str_value] = value_counts.get(str_value, 0) + 1
            if date and (str_value not in value_dates or date > value_dates[str_value]):
                value_dates[str_value] = date

        max_count = max(value_counts.values())
        max_values = [v for v, c in value_counts.items() if c == max_count]

        if len(max_values) == 1:
            return self._string_to_original(max_values[0], original_values)

        # Tie-break: select the value with the latest date
        latest_value = max(
            max_values,
            key=lambda x: value_dates.get(x, '') if value_dates.get(x) else ''
        )
        return self._string_to_original(latest_value, original_values)


    def _merge_field(self, package_data: List[Dict], field: str) -> Any:
        """Merge field values from multiple sources."""
        values = []
        for item in package_data:
            value = item.get(field)
            if value is not None:
                if isinstance(value, list):
                    values.extend(value)
                else:
                    values.append(value)

        if not values:
            return None

        if field in {'Source', 'source_link'}:
            return list(set(str(v) for v in values))

        if self._is_list_field(field, values):
            return list(set(str(x) for x in values))

        latest_item = max(package_data, key=lambda x: x.get('post_date', ''))
        return latest_item.get(field)


def main():
    aggregator = MaliciousPackageAggregator()
    results = aggregator.aggregate_packages(
        'Intelliradar_data.json',
        'aggregated_packages.json'
    )
    print(f"Aggregated {len(results)} packages")


if __name__ == "__main__":
    main()
