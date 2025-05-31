import json
import os
from typing import List, Set

def extract_source_links(json_data: dict) -> List[str]:
    """
    
    """
    links = []
    
    if isinstance(json_data, dict):
        # 检查当前字典是否包含source_link
        if 'source_link' in json_data:
            if isinstance(json_data['source_link'], list):
                links.extend(json_data['source_link'])
            elif isinstance(json_data['source_link'], str):
                links.append(json_data['source_link'])
        
        # 递归处理字典中的所有值
        for value in json_data.values():
            links.extend(extract_source_links(value))
            
    elif isinstance(json_data, list):
        # 递归处理列表中的所有元素
        for item in json_data:
            links.extend(extract_source_links(item))
    
    return links

def process_json_file(file_path: str) -> Set[str]:
    """
    处理单个JSON文件并返回去重后的source_link集合
    """
    try:
        print(f"正在处理文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        links = extract_source_links(data)
        unique_links = set(links)
        print(f"找到 {len(links)} 个source_link，去重后有 {len(unique_links)} 个")
        return unique_links
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return set()

def main():
    # 指定要处理的JSON文件
    json_file = "./name_formated.json"
    
    if len(os.sys.argv) > 1:
        json_file = os.sys.argv[1]
    
    all_source_links = process_json_file(json_file)
    
    print(f"\n去重后的source_link总数: {len(all_source_links)}")
    
    # 是否需要输出所有链接
    if len(all_source_links) <= 100 or input("是否要显示所有链接? (y/n): ").lower() == 'y':
        print("\n所有去重后的source_link:")
        for link in sorted(all_source_links):
            print(f"- {link}")

if __name__ == "__main__":
    main()
