import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from collections import Counter
import numpy as np

# 设置字体和样式
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")

# 读取规范化后的JSON数据
try:
    with open('/Users/blue/Documents/Github/SCC_Intelligence/Codes/Collection/normalized_attack_data.json', 'r', encoding='utf-8') as f:
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
    else:
        return pm

# 收集npm和pypi的攻击向量和攻击方法数据
npm_vectors = []
pypi_vectors = []
npm_methods = []
pypi_methods = []

# 定义npm特有的攻击向量（不应该出现在PyPI中）
npm_only_vectors = {
    'Preinstall_Script', 
    'Postinstall_Script',
    'Post_Installation_Hook'  # 这个也主要是npm的概念
}

# 定义PyPI特有的攻击向量（如果有的话）
pypi_only_vectors = {
    # 可以根据需要添加PyPI特有的攻击向量
}

for item in data:
    pm = normalize_package_manager(item.get("Package Manager", ""))
    vectors = item.get("Attack Vector Normalized", [])
    methods = item.get("Method of Attack Normalized", [])
    
    if pm == "npm":
        if vectors and isinstance(vectors, list):
            # NPM可以使用所有攻击向量
            npm_vectors.extend(vectors)
        if methods and isinstance(methods, list):
            npm_methods.extend(methods)
    elif pm == "pypi":
        if vectors and isinstance(vectors, list):
            # PyPI过滤掉npm特有的攻击向量
            filtered_vectors = [v for v in vectors if v not in npm_only_vectors]
            pypi_vectors.extend(filtered_vectors)
            
            # 如果发现PyPI包使用了npm特有的攻击向量，记录警告
            invalid_vectors = [v for v in vectors if v in npm_only_vectors]
            if invalid_vectors:
                package_name = item.get("Package Name", "Unknown")
                print(f"Warning: PyPI package '{package_name}' incorrectly labeled with npm-specific vectors: {invalid_vectors}")
        
        if methods and isinstance(methods, list):
            pypi_methods.extend(methods)

# 统计攻击向量和方法
npm_vector_counts = Counter(npm_vectors)
pypi_vector_counts = Counter(pypi_vectors)
npm_method_counts = Counter(npm_methods)
pypi_method_counts = Counter(pypi_methods)

# 合并npm和pypi的统计，获取top5
all_vector_counts = Counter()
all_vector_counts.update(npm_vector_counts)
all_vector_counts.update(pypi_vector_counts)

all_method_counts = Counter()
all_method_counts.update(npm_method_counts)
all_method_counts.update(pypi_method_counts)

# 获取top15攻击向量和方法
top15_vectors = [item[0] for item in all_vector_counts.most_common(15)]
top15_methods = [item[0] for item in all_method_counts.most_common(15)]

# 创建攻击向量数据框
vector_data = []
for vector in top15_vectors:
    npm_count = npm_vector_counts.get(vector, 0)
    pypi_count = pypi_vector_counts.get(vector, 0)
    total_count = npm_count + pypi_count
    vector_data.append({
        'Attack Vector': vector.replace('_', ' '),
        'NPM': npm_count,
        'PyPI': pypi_count,
        'Total': total_count
    })

# 创建攻击方法数据框
method_data = []
for method in top15_methods:
    npm_count = npm_method_counts.get(method, 0)
    pypi_count = pypi_method_counts.get(method, 0)
    total_count = npm_count + pypi_count
    method_data.append({
        'Attack Method': method.replace('_', ' '),
        'NPM': npm_count,
        'PyPI': pypi_count,
        'Total': total_count
    })

# 转换为DataFrame并按总数从小到大排序
df_vectors = pd.DataFrame(vector_data)
df_vectors = df_vectors.sort_values('Total', ascending=True)

df_methods = pd.DataFrame(method_data)
df_methods = df_methods.sort_values('Total', ascending=True)

# 创建图表 - 增加高度以适应top15
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 12))

# 配色方案
npm_color = '#FF6B6B'
pypi_color = '#4ECDC4'

# 1. 攻击向量Top5柱状图
y_pos1 = np.arange(len(df_vectors))
width = 0.35

bars1_npm = ax1.barh(y_pos1 - width/2, df_vectors['NPM'], width, 
                     label='NPM', color=npm_color, alpha=0.8)
bars1_pypi = ax1.barh(y_pos1 + width/2, df_vectors['PyPI'], width, 
                      label='PyPI', color=pypi_color, alpha=0.8)

ax1.set_yticks(y_pos1)
ax1.set_yticklabels(df_vectors['Attack Vector'], fontsize=20)
ax1.set_xlabel('Number of Packages', fontsize=20, fontweight='bold')
ax1.set_title('Top 15 Attack Vectors', fontsize=18, fontweight='bold', pad=20)
ax1.legend(fontsize=20)
ax1.grid(True, alpha=0.3, axis='x')

# 添加数值标签 - 攻击向量
for i, (npm_count, pypi_count) in enumerate(zip(df_vectors['NPM'], df_vectors['PyPI'])):
    if npm_count > 0:
        ax1.text(npm_count + max(df_vectors['NPM']) * 0.01, i - width/2, str(npm_count), 
                va='center', ha='left', fontweight='bold', fontsize=18)
    if pypi_count > 0:
        ax1.text(pypi_count + max(df_vectors['PyPI']) * 0.01, i + width/2, str(pypi_count), 
                va='center', ha='left', fontweight='bold', fontsize=18)

# 2. 攻击方法Top5柱状图
y_pos2 = np.arange(len(df_methods))

bars2_npm = ax2.barh(y_pos2 - width/2, df_methods['NPM'], width, 
                     label='NPM', color=npm_color, alpha=0.8)
bars2_pypi = ax2.barh(y_pos2 + width/2, df_methods['PyPI'], width, 
                      label='PyPI', color=pypi_color, alpha=0.8)

ax2.set_yticks(y_pos2)
ax2.set_yticklabels(df_methods['Attack Method'], fontsize=20)
ax2.set_xlabel('Number of Packages', fontsize=20, fontweight='bold')
ax2.set_title('Top 15 Attack Methods', fontsize=18, fontweight='bold', pad=20)
ax2.legend(fontsize=20)
ax2.grid(True, alpha=0.3, axis='x')

# 添加数值标签 - 攻击方法
for i, (npm_count, pypi_count) in enumerate(zip(df_methods['NPM'], df_methods['PyPI'])):
    if npm_count > 0:
        ax2.text(npm_count + max(df_methods['NPM']) * 0.01, i - width/2, str(npm_count), 
                va='center', ha='left', fontweight='bold', fontsize=18)
    if pypi_count > 0:
        ax2.text(pypi_count + max(df_methods['PyPI']) * 0.01, i + width/2, str(pypi_count), 
                va='center', ha='left', fontweight='bold', fontsize=18)

# 调整布局 - 增加更多空间给标题
plt.tight_layout(pad=4.0)

# 添加总体标题 - 调整位置避免超出
fig.suptitle('Top 15 Malicious Package Attack Analysis\nNPM vs PyPI Ecosystems', 
            fontsize=22, fontweight='bold', y=0.99)

# 保存图表 - 更新文件名
plt.savefig('top15_attack_analysis.png', dpi=300, bbox_inches='tight', 
           facecolor='white', edgecolor='none', pad_inches=0.3)
plt.savefig('top15_attack_analysis.pdf', bbox_inches='tight', 
           facecolor='white', edgecolor='none', pad_inches=0.3)

plt.show()

# 打印详细统计
print("\n" + "="*60)
print("TOP 5 攻击向量和方法统计")
print("="*60)

print("\n=== Top 5 攻击向量 (按总数排序) ===")
for i, row in df_vectors.iterrows():
    print(f"{row['Attack Vector']}: NPM={row['NPM']}, PyPI={row['PyPI']}, 总计={row['Total']}")

print("\n=== Top 5 攻击方法 (按总数排序) ===")
for i, row in df_methods.iterrows():
    print(f"{row['Attack Method']}: NPM={row['NPM']}, PyPI={row['PyPI']}, 总计={row['Total']}")

# 计算总体统计
npm_total_vectors = sum(npm_vector_counts.values())
pypi_total_vectors = sum(pypi_vector_counts.values())
npm_total_methods = sum(npm_method_counts.values())
pypi_total_methods = sum(pypi_method_counts.values())

print(f"\n=== 数据验证统计 ===")
print(f"NPM独特攻击向量: {npm_only_vectors}")
print(f"从PyPI数据中过滤的攻击向量实例数: {sum(1 for item in data if normalize_package_manager(item.get('Package Manager', '')) == 'pypi' and any(v in npm_only_vectors for v in item.get('Attack Vector Normalized', [])))}")

print(f"\n=== 总体统计 ===")
print(f"NPM攻击向量总数: {npm_total_vectors}")
print(f"PyPI攻击向量总数: {pypi_total_vectors}")
print(f"NPM攻击方法总数: {npm_total_methods}")
print(f"PyPI攻击方法总数: {pypi_total_methods}")
print(f"独特攻击向量数量: {len(set(npm_vectors + pypi_vectors))}")
print(f"独特攻击方法数量: {len(set(npm_methods + pypi_methods))}")

print("\n图表已保存为:")
print("- top5_attack_analysis.png (高分辨率PNG)")
print("- top5_attack_analysis.pdf (矢量PDF)")