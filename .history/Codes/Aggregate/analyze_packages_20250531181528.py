import json
import os
from collections import Counter, defaultdict

def analyze_packages(file_path):
    stats = {
        "Total packages": 0,
        "pypi packages": 0,
        "npm packages": 0,
        "Attack Vector statistics": Counter(),
        "Method of Attack statistics": Counter(),
        "Version statistics": Counter(),
        "Date of Discovery statistics": Counter(),
        "Repository URL statistics": 0,
        "Indicators of Compromise statistics": 0
    }
    
    unique_values = {
        "Attack Vector": set(),
        "Method of Attack": set(),
        "Version": set(),
        "Date of Discovery": set(),
        "Repository URL": set(),
        "Indicators of Compromise": set()
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        packages = json.load(f)
    
    valid_packages = [pkg for pkg in packages if pkg.get("Package Manager", "").lower() in ["pypi", "npm"]]
    
    stats["Total packages"] = len(valid_packages)
    stats["pypi packages"] = sum(1 for pkg in valid_packages if pkg.get("Package Manager", "").lower() == "pypi")
    stats["npm packages"] = sum(1 for pkg in valid_packages if pkg.get("Package Manager", "").lower() == "npm")
    
    for pkg in valid_packages:
        # Attack Vector 
        attack_vector = pkg.get("Attack Vector")
        if attack_vector and attack_vector != "null" and attack_vector != "":
            if isinstance(attack_vector, list):
                for av in attack_vector:
                    if av and av != "null" and av != "": 
                        stats["Attack Vector statistics"][str(av)] += 1
                        unique_values["Attack Vector"].add(str(av))
            else:
                stats["Attack Vector statistics"][str(attack_vector)] += 1
                unique_values["Attack Vector"].add(str(attack_vector))
        
        # Method of Attack 
        method = pkg.get("Method of Attack")
        if method and method != "null" and method != "":
            if isinstance(method, list):
                for m in method:
                    if m and m != "null" and m != "":  
                        stats["Method of Attack statistics"][str(m)] += 1
                        unique_values["Method of Attack"].add(str(m))
            else:
                stats["Method of Attack statistics"][str(method)] += 1
                unique_values["Method of Attack"].add(str(method))
        
        # Version 
        version = pkg.get("Version")
        if version and version != "null" and version != "":
            if isinstance(version, list):
                for v in version:
                    if v and v != "null" and v != "":  
                        stats["Version statistics"][str(v)] += 1
                        unique_values["Version"].add(str(v))
            else:
                stats["Version statistics"][str(version)] += 1
                unique_values["Version"].add(str(version))
        
        # Date of Discovery 
        date = pkg.get("post_date") or pkg.get("Date of Discovery")
        if date and date != "null" and date != "":
            if isinstance(date, list):
                for d in date:
                    if d and d != "null" and d != "":  
                        stats["Date of Discovery statistics"][str(d)] += 1
                        unique_values["Date of Discovery"].add(str(d))
            else:
                stats["Date of Discovery statistics"][str(date)] += 1
                unique_values["Date of Discovery"].add(str(date))
        
        # Repository URL 
        repo_urls = pkg.get("source_link") or pkg.get("Repository URL")
        if repo_urls and repo_urls != "null":
            if isinstance(repo_urls, list):
                valid_urls = [url for url in repo_urls if url and url != "null" and url != ""]
                stats["Repository URL statistics"] += len(valid_urls)
                for url in valid_urls:
                    unique_values["Repository URL"].add(str(url))
            elif repo_urls:
                stats["Repository URL statistics"] += 1
                unique_values["Repository URL"].add(str(repo_urls))
        
        # Indicators of Compromise
        iocs = pkg.get("Indicators of Compromise")
        if iocs and iocs != "null":
            if isinstance(iocs, list):
                valid_iocs = [ioc for ioc in iocs if ioc and ioc != "null" and ioc != ""]  
                stats["Indicators of Compromise statistics"] += len(valid_iocs)
                for ioc in valid_iocs:
                    unique_values["Indicators of Compromise"].add(str(ioc))
            elif iocs:
                stats["Indicators of Compromise statistics"] += 1
                unique_values["Indicators of Compromise"].add(str(iocs))
    
    print(f"Total packages: {stats['Total packages']}")
    print(f"pypi packages: {stats['pypi packages']}")
    print(f"npm packages: {stats['npm packages']}")
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