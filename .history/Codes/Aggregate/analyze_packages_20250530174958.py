import json
import os
from collections import Counter, defaultdict

def analyze_packages(file_path):
    # 统计结果
    stats = {
        "总包数量": 0,
        "pypi包数量": 0,
        "npm包数量": 0,
        "Attack Vector统计": Counter(),
        "Method of Attack统计": Counter(),
        "Version统计": Counter(),
        "Date of Discovery统计": Counter(),
        "Repository URL数量": 0,
        "Indicators of Compromise总数": 0
    }
    
    # 用于存储唯一值的集合
    unique_values = {
        "Attack Vector": set(),
        "Method of Attack": set(),
        "Version": set(),
        "Date of Discovery": set(),
        "Repository URL": set(),
        "Indicators of Compromise": set()
    }
    
    # 读取JSON文件
    with open(file_path, 'r', encoding='utf-8') as f:
        packages = json.load(f)
    
    # 只考虑pypi和npm包
    valid_packages = [pkg for pkg in packages if pkg.get("Package Manager", "").lower() in ["pypi", "npm"]]
    
    stats["总包数量"] = len(valid_packages)
    stats["pypi包数量"] = sum(1 for pkg in valid_packages if pkg.get("Package Manager", "").lower() == "pypi")
    stats["npm包数量"] = sum(1 for pkg in valid_packages if pkg.get("Package Manager", "").lower() == "npm")
    
    # 统计各个字段
    for pkg in valid_packages:
        # Attack Vector - 可能是字符串或列表
        attack_vector = pkg.get("Attack Vector")
        if attack_vector and attack_vector != "null" and attack_vector != "":
            if isinstance(attack_vector, list):
                for av in attack_vector:
                    if av and av != "null" and av != "":  # 确保不为null或空
                        stats["Attack Vector统计"][str(av)] += 1
                        unique_values["Attack Vector"].add(str(av))
            else:
                stats["Attack Vector统计"][str(attack_vector)] += 1
                unique_values["Attack Vector"].add(str(attack_vector))
        
        # Method of Attack - 可能是字符串或列表
        method = pkg.get("Method of Attack")
        if method and method != "null" and method != "":
            if isinstance(method, list):
                for m in method:
                    if m and m != "null" and m != "":  # 确保不为null或空
                        stats["Method of Attack统计"][str(m)] += 1
                        unique_values["Method of Attack"].add(str(m))
            else:
                stats["Method of Attack统计"][str(method)] += 1
                unique_values["Method of Attack"].add(str(method))
        
        # Version - 可能在不同字段中
        version = pkg.get("Version")
        if version and version != "null" and version != "":
            if isinstance(version, list):
                for v in version:
                    if v and v != "null" and v != "":  # 确保不为null或空
                        stats["Version统计"][str(v)] += 1
                        unique_values["Version"].add(str(v))
            else:
                stats["Version统计"][str(version)] += 1
                unique_values["Version"].add(str(version))
        
        # Date of Discovery (可能是post_date或Date of Discovery)
        date = pkg.get("post_date") or pkg.get("Date of Discovery")
        if date and date != "null" and date != "":
            if isinstance(date, list):
                for d in date:
                    if d and d != "null" and d != "":  # 确保不为null或空
                        stats["Date of Discovery统计"][str(d)] += 1
                        unique_values["Date of Discovery"].add(str(d))
            else:
                stats["Date of Discovery统计"][str(date)] += 1
                unique_values["Date of Discovery"].add(str(date))
        
        # Repository URL (可能在source_link或其他字段)
        repo_urls = pkg.get("source_link") or pkg.get("Repository URL")
        if repo_urls and repo_urls != "null":
            if isinstance(repo_urls, list):
                valid_urls = [url for url in repo_urls if url and url != "null" and url != ""]
                stats["Repository URL数量"] += len(valid_urls)
                for url in valid_urls:
                    unique_values["Repository URL"].add(str(url))
            elif repo_urls:
                stats["Repository URL数量"] += 1
                unique_values["Repository URL"].add(str(repo_urls))
        
        # Indicators of Compromise
        iocs = pkg.get("Indicators of Compromise")
        if iocs and iocs != "null":
            if isinstance(iocs, list):
                valid_iocs = [ioc for ioc in iocs if ioc and ioc != "null" and ioc != ""]  # 过滤掉None和空值
                stats["Indicators of Compromise总数"] += len(valid_iocs)
                for ioc in valid_iocs:
                    unique_values["Indicators of Compromise"].add(str(ioc))
            elif iocs:
                stats["Indicators of Compromise总数"] += 1
                unique_values["Indicators of Compromise"].add(str(iocs))
    
    # 打印结果
    print(f"总包数量: {stats['总包数量']}")
    print(f"pypi包数量: {stats['pypi包数量']}")
    print(f"npm包数量: {stats['npm包数量']}")
    print(f"\n不同Attack Vector数量: {len(unique_values['Attack Vector'])}")
    print(f"不同Method of Attack数量: {len(unique_values['Method of Attack'])}")
    print(f"不同Version数量: {len(unique_values['Version'])}")
    print(f"不同Date of Discovery数量: {len(unique_values['Date of Discovery'])}")
    print(f"不同Repository URL数量: {len(unique_values['Repository URL'])}")
    print(f"不同Indicators of Compromise数量: {len(unique_values['Indicators of Compromise'])}")
    print(f"Indicators of Compromise总数: {stats['Indicators of Compromise总数']}")
    
    # 打印各个值的前5个示例
    for field, values in unique_values.items():
        values_list = list(values)
        if values_list:
            print(f"\n{field}前5个示例:")
            for i, value in enumerate(values_list[:5]):
                print(f"  {i+1}. {value}")
    
    # 返回结果
    return stats, unique_values


if __name__ == "__main__":
    file_path = "/Users/blue/Documents/Github/SCC_Intelligence/Codes/Aggregate/aggregated_packages.json"
    if not os.path.exists(file_path):
        print(f"错误: 找不到文件 {file_path}")
    else:
        analyze_packages(file_path) 