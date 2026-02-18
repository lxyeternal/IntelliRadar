import json
from collections import Counter, defaultdict
import sys
from datetime import datetime

# 创建输出文件
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"normalized_attack_distribution_{timestamp}.txt"

# 重定向输出到文件和控制台
class TeeOutput:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.file = open(filename, "w", encoding="utf-8")
        
    def write(self, message):
        self.terminal.write(message)
        self.file.write(message)
        
    def flush(self):
        self.terminal.flush()
        self.file.flush()

sys.stdout = TeeOutput(output_file)

# 读取规范化后的JSON数据
try:
    with open('normalized_attack_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"成功读取规范化数据，共 {len(data)} 条记录")
except Exception as e:
    print(f"读取文件时出错: {e}")
    exit(1)

# 标准化包管理器名称
def normalize_package_manager(pm):
    if not pm:
        return "unknown"
    
    pm = str(pm).lower().strip()
    
    if pm in ["npm", "js", "javascript", "node", "nodejs"]:
        return "npm"
    elif pm in ["pypi", "python", "pip", "pypl"]:
        return "pypi"
    elif pm in ["nuget", ".net", "dotnet"]:
        return "nuget"
    elif pm in ["maven", "java"]:
        return "maven"
    elif pm in ["rubygems", "ruby", "gem"]:
        return "rubygems"
    elif pm in ["composer", "php"]:
        return "composer"
    elif pm in ["cargo", "rust"]:
        return "cargo"
    else:
        return pm

# 处理数据
package_managers = []
normalized_attack_methods = []
normalized_attack_vectors = []
package_names = []
packages_by_pm = {}  # 按包管理器分类的包名

# 多攻击方法/向量统计
multi_method_packages = []
multi_vector_packages = []
method_count_distribution = Counter()
vector_count_distribution = Counter()

for item in data:
    pm = item.get("Package Manager")
    name = item.get("Package Name")
    methods = item.get("Method of Attack Normalized", [])
    vectors = item.get("Attack Vector Normalized", [])
    
    if name:
        package_names.append(name)
    
    if pm:
        normalized_pm = normalize_package_manager(pm)
        package_managers.append(normalized_pm)
        
        # 按包管理器收集包名
        if normalized_pm not in packages_by_pm:
            packages_by_pm[normalized_pm] = set()
        packages_by_pm[normalized_pm].add(name)
    
    # 处理规范化的攻击方法
    if methods and isinstance(methods, list):
        normalized_attack_methods.extend(methods)
        method_count = len(methods)
        method_count_distribution[method_count] += 1
        
        # 记录多攻击方法的包
        if method_count >= 2:
            multi_method_packages.append({
                'name': name,
                'pm': normalized_pm if pm else 'unknown',
                'methods': methods,
                'count': method_count
            })
    
    # 处理规范化的攻击向量
    if vectors and isinstance(vectors, list):
        normalized_attack_vectors.extend(vectors)
        vector_count = len(vectors)
        vector_count_distribution[vector_count] += 1
        
        # 记录多攻击向量的包
        if vector_count >= 2:
            multi_vector_packages.append({
                'name': name,
                'pm': normalized_pm if pm else 'unknown',
                'vectors': vectors,
                'count': vector_count
            })

# 统计结果
pm_counter = Counter(package_managers)

# 按包管理器分组的攻击统计
pm_method_stats = defaultdict(list)
pm_vector_stats = defaultdict(list)

for item in data:
    pm = normalize_package_manager(item.get("Package Manager", "unknown"))
    methods = item.get("Method of Attack Normalized", [])
    vectors = item.get("Attack Vector Normalized", [])
    
    if methods and isinstance(methods, list):
        pm_method_stats[pm].extend(methods)
    
    if vectors and isinstance(vectors, list):
        pm_vector_stats[pm].extend(vectors)

# 打印统计结果
print("\n" + "="*80)
print("规范化攻击数据分析报告")
print("="*80)

# 基本统计
print("\n=== 基本统计信息 ===")
print(f"总记录数: {len(data)}")
print(f"总包名数: {len(set(package_names))}")
print(f"总攻击方法数: {len(normalized_attack_methods)}")
print(f"总攻击向量数: {len(normalized_attack_vectors)}")
print(f"独立攻击方法数: {len(set(normalized_attack_methods))}")
print(f"独立攻击向量数: {len(set(normalized_attack_vectors))}")

# 多攻击方法/向量统计
print(f"\n=== 多攻击方法/向量包统计 ===")
print(f"具有2个以上攻击方法的包: {len(multi_method_packages)} 个")
print(f"具有2个以上攻击向量的包: {len(multi_vector_packages)} 个")

print(f"\n攻击方法数量分布:")
for count in sorted(method_count_distribution.keys()):
    packages_count = method_count_distribution[count]
    percentage = (packages_count / len(data)) * 100
    print(f"  {count}个方法: {packages_count} 包 ({percentage:.1f}%)")

print(f"\n攻击向量数量分布:")
for count in sorted(vector_count_distribution.keys()):
    packages_count = vector_count_distribution[count]
    percentage = (packages_count / len(data)) * 100
    print(f"  {count}个向量: {packages_count} 包 ({percentage:.1f}%)")

# npm和pypi统计
print(f"\n=== npm和pypi包管理器统计 ===")
for pm in ["npm", "pypi"]:
    if pm in pm_counter:
        unique_packages = len(packages_by_pm.get(pm, set()))
        print(f"{pm}: {pm_counter[pm]} 条记录, {unique_packages} 个独立包")

# npm和pypi的综合攻击方法统计
npm_pypi_methods = []
npm_pypi_vectors = []
npm_pypi_packages = set()

for pm in ["npm", "pypi"]:
    if pm in pm_method_stats:
        npm_pypi_methods.extend(pm_method_stats[pm])
    if pm in pm_vector_stats:
        npm_pypi_vectors.extend(pm_vector_stats[pm])
    if pm in packages_by_pm:
        npm_pypi_packages.update(packages_by_pm[pm])

print(f"\n=== npm和pypi综合攻击方法统计 (共 {len(npm_pypi_methods)} 个方法实例, {len(npm_pypi_packages)} 个独立包) ===")
if npm_pypi_methods:
    npm_pypi_method_counter = Counter(npm_pypi_methods)
    for method, count in npm_pypi_method_counter.most_common():
        percentage = (count / len(npm_pypi_methods)) * 100
        print(f"  {method}: {count} ({percentage:.1f}%)")

print(f"\n=== npm和pypi综合攻击向量统计 (共 {len(npm_pypi_vectors)} 个向量实例) ===")
if npm_pypi_vectors:
    npm_pypi_vector_counter = Counter(npm_pypi_vectors)
    for vector, count in npm_pypi_vector_counter.most_common():
        percentage = (count / len(npm_pypi_vectors)) * 100
        print(f"  {vector}: {count} ({percentage:.1f}%)")

# npm和pypi单独统计
print(f"\n=== npm和pypi单独攻击方法统计 ===")
for pm in ["npm", "pypi"]:
    if pm in pm_method_stats and len(pm_method_stats[pm]) > 0:
        print(f"\n{pm} 包管理器攻击方法 (共 {len(pm_method_stats[pm])} 个方法实例, {len(packages_by_pm.get(pm, set()))} 个独立包):")
        method_count = Counter(pm_method_stats[pm])
        total = len(pm_method_stats[pm])
        for method, count in method_count.most_common():
            percentage = (count / total) * 100
            print(f"  {method}: {count} ({percentage:.1f}%)")

print(f"\n=== npm和pypi单独攻击向量统计 ===")
for pm in ["npm", "pypi"]:
    if pm in pm_vector_stats and len(pm_vector_stats[pm]) > 0:
        print(f"\n{pm} 包管理器攻击向量 (共 {len(pm_vector_stats[pm])} 个向量实例):")
        vector_count = Counter(pm_vector_stats[pm])
        total = len(pm_vector_stats[pm])
        for vector, count in vector_count.most_common():
            percentage = (count / total) * 100
            print(f"  {vector}: {count} ({percentage:.1f}%)")

# 详细的多攻击方法包列表
print(f"\n=== 具有多个攻击方法的包详情 ===")
if multi_method_packages:
    # 按攻击方法数量排序
    multi_method_packages.sort(key=lambda x: x['count'], reverse=True)
    for pkg in multi_method_packages[:20]:  # 显示前20个
        print(f"  {pkg['name']} ({pkg['pm']}): {pkg['count']}个方法 - {', '.join(pkg['methods'])}")
    
    if len(multi_method_packages) > 20:
        print(f"  ... 还有 {len(multi_method_packages) - 20} 个包")

# 详细的多攻击向量包列表
print(f"\n=== 具有多个攻击向量的包详情 ===")
if multi_vector_packages:
    # 按攻击向量数量排序
    multi_vector_packages.sort(key=lambda x: x['count'], reverse=True)
    for pkg in multi_vector_packages[:20]:  # 显示前20个
        print(f"  {pkg['name']} ({pkg['pm']}): {pkg['count']}个向量 - {', '.join(pkg['vectors'])}")
    
    if len(multi_vector_packages) > 20:
        print(f"  ... 还有 {len(multi_vector_packages) - 20} 个包")

# 全部攻击方法排行
print(f"\n=== 所有攻击方法排行 ===")
all_methods_counter = Counter(normalized_attack_methods)
for method, count in all_methods_counter.most_common():
    percentage = (count / len(normalized_attack_methods)) * 100
    print(f"  {method}: {count} ({percentage:.1f}%)")

# 全部攻击向量排行
print(f"\n=== 所有攻击向量排行 ===")
all_vectors_counter = Counter(normalized_attack_vectors)
for vector, count in all_vectors_counter.most_common():
    percentage = (count / len(normalized_attack_vectors)) * 100
    print(f"  {vector}: {count} ({percentage:.1f}%)")

# 恢复标准输出并关闭文件
sys.stdout = sys.__stdout__
print(f"\n结果已保存到文件: {output_file}")