import json
from collections import Counter, defaultdict
import sys
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"normalized_attack_distribution_{timestamp}.txt"


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

try:
    with open('normalized_attack_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Successfully loaded normalized data, {len(data)} records total")
except Exception as e:
    print(f"Error reading file: {e}")
    exit(1)


def normalize_package_manager(pm):
    """Normalize package manager name to canonical form"""
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


package_managers = []
normalized_attack_methods = []
normalized_attack_vectors = []
package_names = []
packages_by_pm = {}

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

        if normalized_pm not in packages_by_pm:
            packages_by_pm[normalized_pm] = set()
        packages_by_pm[normalized_pm].add(name)

    if methods and isinstance(methods, list):
        normalized_attack_methods.extend(methods)
        method_count = len(methods)
        method_count_distribution[method_count] += 1

        if method_count >= 2:
            multi_method_packages.append({
                'name': name,
                'pm': normalized_pm if pm else 'unknown',
                'methods': methods,
                'count': method_count
            })

    if vectors and isinstance(vectors, list):
        normalized_attack_vectors.extend(vectors)
        vector_count = len(vectors)
        vector_count_distribution[vector_count] += 1

        if vector_count >= 2:
            multi_vector_packages.append({
                'name': name,
                'pm': normalized_pm if pm else 'unknown',
                'vectors': vectors,
                'count': vector_count
            })

pm_counter = Counter(package_managers)

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

print("\n" + "="*80)
print("Normalized Attack Data Analysis Report")
print("="*80)

print("\n=== Basic Statistics ===")
print(f"Total records: {len(data)}")
print(f"Total package names: {len(set(package_names))}")
print(f"Total attack methods: {len(normalized_attack_methods)}")
print(f"Total attack vectors: {len(normalized_attack_vectors)}")
print(f"Unique attack methods: {len(set(normalized_attack_methods))}")
print(f"Unique attack vectors: {len(set(normalized_attack_vectors))}")

print(f"\n=== Multi-Attack Method/Vector Package Statistics ===")
print(f"Packages with 2+ attack methods: {len(multi_method_packages)}")
print(f"Packages with 2+ attack vectors: {len(multi_vector_packages)}")

print(f"\nAttack method count distribution:")
for count in sorted(method_count_distribution.keys()):
    packages_count = method_count_distribution[count]
    percentage = (packages_count / len(data)) * 100
    print(f"  {count} methods: {packages_count} packages ({percentage:.1f}%)")

print(f"\nAttack vector count distribution:")
for count in sorted(vector_count_distribution.keys()):
    packages_count = vector_count_distribution[count]
    percentage = (packages_count / len(data)) * 100
    print(f"  {count} vectors: {packages_count} packages ({percentage:.1f}%)")

print(f"\n=== npm and pypi Package Manager Statistics ===")
for pm in ["npm", "pypi"]:
    if pm in pm_counter:
        unique_packages = len(packages_by_pm.get(pm, set()))
        print(f"{pm}: {pm_counter[pm]} records, {unique_packages} unique packages")

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

print(f"\n=== npm+pypi Combined Attack Method Statistics ({len(npm_pypi_methods)} method instances, {len(npm_pypi_packages)} unique packages) ===")
if npm_pypi_methods:
    npm_pypi_method_counter = Counter(npm_pypi_methods)
    for method, count in npm_pypi_method_counter.most_common():
        percentage = (count / len(npm_pypi_methods)) * 100
        print(f"  {method}: {count} ({percentage:.1f}%)")

print(f"\n=== npm+pypi Combined Attack Vector Statistics ({len(npm_pypi_vectors)} vector instances) ===")
if npm_pypi_vectors:
    npm_pypi_vector_counter = Counter(npm_pypi_vectors)
    for vector, count in npm_pypi_vector_counter.most_common():
        percentage = (count / len(npm_pypi_vectors)) * 100
        print(f"  {vector}: {count} ({percentage:.1f}%)")

print(f"\n=== npm and pypi Individual Attack Method Statistics ===")
for pm in ["npm", "pypi"]:
    if pm in pm_method_stats and len(pm_method_stats[pm]) > 0:
        print(f"\n{pm} attack methods ({len(pm_method_stats[pm])} method instances, {len(packages_by_pm.get(pm, set()))} unique packages):")
        method_count = Counter(pm_method_stats[pm])
        total = len(pm_method_stats[pm])
        for method, count in method_count.most_common():
            percentage = (count / total) * 100
            print(f"  {method}: {count} ({percentage:.1f}%)")

print(f"\n=== npm and pypi Individual Attack Vector Statistics ===")
for pm in ["npm", "pypi"]:
    if pm in pm_vector_stats and len(pm_vector_stats[pm]) > 0:
        print(f"\n{pm} attack vectors ({len(pm_vector_stats[pm])} vector instances):")
        vector_count = Counter(pm_vector_stats[pm])
        total = len(pm_vector_stats[pm])
        for vector, count in vector_count.most_common():
            percentage = (count / total) * 100
            print(f"  {vector}: {count} ({percentage:.1f}%)")

print(f"\n=== Packages with Multiple Attack Methods (Details) ===")
if multi_method_packages:
    multi_method_packages.sort(key=lambda x: x['count'], reverse=True)
    for pkg in multi_method_packages[:20]:
        print(f"  {pkg['name']} ({pkg['pm']}): {pkg['count']} methods - {', '.join(pkg['methods'])}")

    if len(multi_method_packages) > 20:
        print(f"  ... and {len(multi_method_packages) - 20} more packages")

print(f"\n=== Packages with Multiple Attack Vectors (Details) ===")
if multi_vector_packages:
    multi_vector_packages.sort(key=lambda x: x['count'], reverse=True)
    for pkg in multi_vector_packages[:20]:
        print(f"  {pkg['name']} ({pkg['pm']}): {pkg['count']} vectors - {', '.join(pkg['vectors'])}")

    if len(multi_vector_packages) > 20:
        print(f"  ... and {len(multi_vector_packages) - 20} more packages")

print(f"\n=== All Attack Methods Ranking ===")
all_methods_counter = Counter(normalized_attack_methods)
for method, count in all_methods_counter.most_common():
    percentage = (count / len(normalized_attack_methods)) * 100
    print(f"  {method}: {count} ({percentage:.1f}%)")

print(f"\n=== All Attack Vectors Ranking ===")
all_vectors_counter = Counter(normalized_attack_vectors)
for vector, count in all_vectors_counter.most_common():
    percentage = (count / len(normalized_attack_vectors)) * 100
    print(f"  {vector}: {count} ({percentage:.1f}%)")

sys.stdout = sys.__stdout__
print(f"\nResults saved to file: {output_file}")
