import json
from typing import List, Dict, Any, Set
from datetime import datetime


class MaliciousPackageAggregator:
    def __init__(self):
        # 必定是字符串的字段
        self.string_fields = {
            'Package Name',
            'Package Manager'
        }

        # 需要投票的字段
        self.voting_fields = {
            'Method of Attack',
            'Attack Vector',
            'Discoverer',
            'Impacted Systems',
            'Date of Discovery'
        }

        # 需要合并的字段
        self.merge_fields = {
            'Indicators of Compromise',
            'Source',
            'source_link'
        }

    def _value_to_string(self, value: Any) -> str:
        """将任意值转换为可哈希的字符串形式"""
        if isinstance(value, list):
            # 列表转换为排序后的字符串
            return ','.join(sorted(str(x) for x in value))
        return str(value)

    def _string_to_original(self, string_value: str, original_values: List[Any]) -> Any:
        """将字符串形式转换回原始类型"""
        # 在原始值中查找匹配的值
        for value in original_values:
            if self._value_to_string(value) == string_value:
                return value
        return string_value  # 如果找不到匹配的，返回字符串

    def aggregate_packages(self, input_file: str, output_file: str):
        """主聚合流程"""
        # 1. 读取数据
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 2. 按包管理器和包名分组
        grouped_data = self._group_by_manager_and_name(data)

        # 3. 聚合每组数据
        aggregated_results = []
        for package_manager, packages in grouped_data.items():
            for package_name, package_data in packages.items():
                aggregated_package = self._aggregate_single_package(
                    package_data,
                    package_manager,
                    package_name
                )
                aggregated_results.append(aggregated_package)

        # 4. 写入结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated_results, f, indent=2, ensure_ascii=False)

        return aggregated_results

    def _group_by_manager_and_name(self, data: List[Dict]) -> Dict:
        """按包管理器和包名分组"""
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
        """聚合单个包的所有数据"""
        result = {
            'Package Name': package_name,
            'Package Manager': package_manager
        }

        # 获取所有存在的字段
        all_fields = set()
        for item in package_data:
            all_fields.update(item.keys())

        # 处理每个字段
        for field in all_fields:
            # 跳过已处理的字段
            if field in result:
                continue

            if field in self.voting_fields:
                result[field] = self._vote_field(package_data, field)
            else:
                result[field] = self._merge_field(package_data, field)

        return result

    def _is_list_field(self, field: str, values: List[Any]) -> bool:
        """判断一个字段是否应该被视为列表类型"""
        if field in self.string_fields:
            return False
        return any(isinstance(v, list) for v in values if v is not None)

    def _vote_field(self, package_data: List[Dict], field: str) -> Any:
        """字段投票逻辑"""
        # 收集非空值
        values = []
        original_values = []  # 保存原始值
        for item in package_data:
            value = item.get(field)
            if value is not None:  # 只排除None
                values.append((self._value_to_string(value), item.get('post_date', '')))
                original_values.append(value)

        if not values:
            return None

        if len(values) == 1:
            return original_values[0]

        # 统计每个值的出现次数
        value_counts = {}
        value_dates = {}  # 记录每个值最新的日期
        for str_value, date in values:
            value_counts[str_value] = value_counts.get(str_value, 0) + 1
            if date and (str_value not in value_dates or date > value_dates[str_value]):
                value_dates[str_value] = date

        # 找出得票最多的值
        max_count = max(value_counts.values())
        max_values = [v for v, c in value_counts.items() if c == max_count]

        if len(max_values) == 1:
            return self._string_to_original(max_values[0], original_values)

        # 如果有多个最高票数，选择最新的
        latest_value = max(
            max_values,
            key=lambda x: value_dates.get(x, '') if value_dates.get(x) else ''
        )
        return self._string_to_original(latest_value, original_values)

    def _merge_field(self, package_data: List[Dict], field: str) -> Any:
        """字段合并逻辑"""
        values = []
        for item in package_data:
            value = item.get(field)
            if value is not None:  # 只排除None
                if isinstance(value, list):
                    values.extend(value)
                else:
                    values.append(value)

        if not values:
            return None

        # 针对特定字段的处理
        if field in {'Source', 'source_link'}:
            # Source 和 source_link 要合并成列表
            return list(set(str(v) for v in values))

        # 判断字段类型
        if self._is_list_field(field, values):
            # 合并列表类型的字段
            return list(set(str(x) for x in values))

        # 对于非列表字段，使用最新记录的值
        latest_item = max(package_data, key=lambda x: x.get('post_date', ''))
        return latest_item.get(field)


def main():
    # 使用示例
    aggregator = MaliciousPackageAggregator()
    results = aggregator.aggregate_packages(
        'Intelliradar_data.json',
        'aggregated_packages.json'
    )
    print(f"Aggregated {len(results)} packages")


if __name__ == "__main__":
    main()