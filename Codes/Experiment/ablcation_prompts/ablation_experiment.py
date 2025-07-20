#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : ablation_experiment
# @Project  : SCC_Intelligence
# Time      : 2024-07-16
# Author    : blue
# version   : python
# Description：执行提示词对比实验
"""

import os
import json
import time
import re
import nltk
import openai
from openai import AzureOpenAI
import multiprocessing
from multiprocessing import Pool, Lock
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
from functools import partial
from nltk.corpus import stopwords

# 下载停用词
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

# 创建一个全局锁，用于安全打印
print_lock = Lock()

def safe_print(*args, **kwargs):
    """线程安全的打印函数"""
    with print_lock:
        print(*args, **kwargs)

def read_file(file_path: str) -> str:
    """读取文件内容"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def save_json(data, file_path: str):
    """保存数据到JSON文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(data)
    safe_print(f"结果已保存到: {file_path}")

def load_common_words(common_words_file: str) -> set:
    """加载常用词列表"""
    common_words = set()
    with open(common_words_file, 'r', encoding='utf-8') as file:
        for line in file:
            common_words.add(line.strip().lower())
    return common_words

def extract_package_names(content: str, regex: str, common_words: set) -> list:
    """提取潜在的包名"""
    try:
        matches = re.findall(regex, content)
        unique_matches = set(matches)
        unique_words = []
        
        for word in unique_matches:
            if word.endswith(".") or word.endswith(","):
                word = word[:-1]
            
            if word.lower() not in common_words and word not in stop_words:
                unique_words.append(word)
                
        return unique_words
    except Exception as e:
        safe_print(f"提取包名时出错: {e}")
        return []

# def gpt4o_query(messages: list, max_attempts: int = 5, 
#               response_format: Optional[Dict] = None) -> str:
#     """使用GPT-4o执行查询"""
#     api_key = "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"
#     client = openai.OpenAI(api_key=api_key)
    
#     wait_time = 10
#     attempt = 0
    
#     while attempt < max_attempts:
#         try:
#             completion = client.chat.completions.create(
#                 model="gpt-4o",
#                 messages=messages,
#                 response_format={"type": "json_object"},
#                 temperature=0,
#                 max_tokens=16000,
#                 top_p=0.3,
#                 frequency_penalty=0,
#                 presence_penalty=0,
#                 stop=None,
#                 stream=False,
#                 seed=42
#             )
#             return completion.choices[0].message.content
#         except Exception as e:
#             safe_print(f"尝试 {attempt + 1} 失败: {e}")
#             attempt += 1
#             time.sleep(wait_time)
#             wait_time += 5
    
#     return ""


def gpt4o_query(messages: list, max_attempts: int = 5, 
              response_format: Optional[Dict] = None) -> str:
    """使用GPT-4o执行查询"""
    azure_api_base = "https://malicious-intelligence.openai.azure.com/"
    azure_api_version = "2024-02-15-preview"
    azure_api_key = "65fda776b8af45bd943e2bbd15773ab0"
    api_key = azure_api_key
    client = AzureOpenAI(api_key=api_key, api_base=azure_api_base, api_version=azure_api_version)
    
    wait_time = 10
    attempt = 0
    
    while attempt < max_attempts:
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=16000,
                top_p=0.3,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False,
                seed=42
            )
            return completion.choices[0].message.content
        except Exception as e:
            safe_print(f"尝试 {attempt + 1} 失败: {e}")
            attempt += 1
            time.sleep(wait_time)
            wait_time += 5
    
    return ""

def process_with_single_prompt(content: str, potential_entities: list, 
                              prompt: str, version: str, entity_definitions: str) -> str:
    """使用单一提示词处理内容"""
    message_text = [
        {"role": "system", "content": "You are a cybersecurity expert specializing in analyzing malicious packages in package managers."},
        {"role": "user", "content": f"""
            === SOURCE CONTENT ===
            {content}

            === INSTRUCTIONS ===
            {prompt}
        """}
    ]
    
    return gpt4o_query(message_text, response_format={"type": "json_object"})

def process_with_three_steps(content: str, potential_entities: list, 
                            extract_prompt: str, relation_prompt: str, verify_prompt: str,
                            version: str, entity_definitions: str) -> Tuple[str, str, str]:
    """使用三步骤提示词处理内容"""
    # 步骤1: 实体提取
    if version.startswith("v9"):
        # v9版本第一步不包含潜在恶意包名列表，但包含实体定义
        extract_message = [
            {"role": "system", "content": "You are a cybersecurity expert specializing in analyzing malicious packages in package managers."},
            {"role": "user", "content": f"""
                === SOURCE CONTENT ===
                {content}

                === ENTITY DEFINITIONS ===
                {entity_definitions}

                === EXTRACTION INSTRUCTIONS ===
                {extract_prompt}
            """}
        ]
    else:
        extract_message = [
            {"role": "system", "content": "You are a cybersecurity expert specializing in analyzing malicious packages in package managers."},
            {"role": "user", "content": f"""
                === SOURCE CONTENT ===
                {content}

                === POTENTIAL MALICIOUS PACKAGES ===
                {str(potential_entities)}

                === ENTITY DEFINITIONS ===
                {entity_definitions}

                === EXTRACTION INSTRUCTIONS ===
                {extract_prompt}
            """}
        ]
    
    extract_result = gpt4o_query(extract_message, response_format={"type": "json_object"})
    
    # 步骤2: 实体关系
    relation_message = [
        {"role": "system", "content": "You are a cybersecurity expert specializing in analyzing relationships between entities in malicious package reports."},
        {"role": "user", "content": f"""
            === SOURCE CONTENT ===
            {content}

            === EXTRACTED ENTITIES ===
            {extract_result}


            === RELATIONSHIP ANALYSIS INSTRUCTIONS ===
            {relation_prompt}
        """}
    ]
    
    relation_result = gpt4o_query(relation_message, response_format={"type": "json_object"})
    
    # 步骤3: 信息验证
    verify_message = [
        {"role": "system", "content": "You are a cybersecurity expert specializing in verifying the accuracy of extracted information about malicious packages."},
        {"role": "user", "content": f"""
            === SOURCE CONTENT ===
            {content}

            === EXTRACTED ENTITIES AND RELATIONS ===
            {relation_result}


            === VERIFICATION INSTRUCTIONS ===
            {verify_prompt}
        """}
    ]
    
    verify_result = gpt4o_query(verify_message, response_format={"type": "json_object"})
    
    return extract_result, relation_result, verify_result

def process_file_task(task_data: tuple) -> str:
    """处理单个文件的任务"""
    (
        file_path, file_name, version_prompts, output_base_dir, 
        common_words, regex, entity_definitions
    ) = task_data
    
    try:
        pid = os.getpid()
        safe_print(f"[进程 {pid}] 开始处理: {file_name} - 版本 {list(version_prompts.keys())}")
        
        # 读取文件内容
        content = read_file(file_path)
        
        # 提取潜在包名
        potential_entities = extract_package_names(content, regex, common_words)
        
        # 处理每个版本的提示词
        for version, prompts in version_prompts.items():
            safe_print(f"[进程 {pid}] {file_name} - 处理版本 {version}")
            
            # 生成输出文件名的基础部分
            base_name = os.path.splitext(file_name)[0]
            
            # 根据提示词数量决定处理方式
            if len(prompts) == 1:
                # 单一提示词处理
                prompt = prompts[0]
                result = process_with_single_prompt(content, potential_entities, prompt, version, entity_definitions)
                
                # 保存结果
                output_path = os.path.join(output_base_dir, version, f"{base_name}.json")
                save_json(result, output_path)
                safe_print(f"[进程 {pid}] {file_name} - 版本 {version} - 完成单一提示词处理")
                
            elif len(prompts) == 3:
                # 三步骤处理
                extract_prompt, relation_prompt, verify_prompt = prompts
                extract_result, relation_result, verify_result = process_with_three_steps(
                    content, potential_entities, extract_prompt, relation_prompt, verify_prompt,
                    version, entity_definitions
                )
                
                # 保存三个步骤的结果
                extract_path = os.path.join(output_base_dir, version, f"{base_name}_extract.json")
                relation_path = os.path.join(output_base_dir, version, f"{base_name}_relation.json")
                verify_path = os.path.join(output_base_dir, version, f"{base_name}_verify.json")
                
                save_json(extract_result, extract_path)
                save_json(relation_result, relation_path)
                save_json(verify_result, verify_path)
                
                safe_print(f"[进程 {pid}] {file_name} - 版本 {version} - 完成三步骤处理")
        
        safe_print(f"[进程 {pid}] 完成处理: {file_name}")
        return file_name
    
    except Exception as e:
        safe_print(f"[进程 {pid}] 处理 {file_name} 时出错: {str(e)}")
        return None

def load_prompt_versions(prompts_dir: str) -> Dict[str, List[str]]:
    """加载所有版本的提示词"""
    version_prompts = {}
    
    # 遍历提示词目录
    for version_dir in os.listdir(prompts_dir):
        if not os.path.isdir(os.path.join(prompts_dir, version_dir)):
            continue
        
        # 确定版本号
        version = version_dir.split('-')[0]  # 提取v1, v2等
        
        # 读取该版本的所有提示词文件
        prompt_files = [f for f in os.listdir(os.path.join(prompts_dir, version_dir)) 
                       if f.endswith('.txt') and not f.startswith('.')]
        
        prompts = []
        for prompt_file in sorted(prompt_files):  # 排序确保顺序一致
            prompt_path = os.path.join(prompts_dir, version_dir, prompt_file)
            prompt_content = read_file(prompt_path)
            prompts.append(prompt_content)
        
        if prompts:  # 只有当有提示词时才添加
            version_prompts[version] = prompts
    
    return version_prompts

def main():
    # 设置多进程启动方法
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        pass
    
    # 设置基础路径
    project_dir = "/Users/blue/Documents/Github/SCC_Intelligence"
    prompts_dir = os.path.join(project_dir, "Codes/Experiment/major/review-d/ablcation_prompts/prompts")
    input_dir = os.path.join(project_dir, "Codes/Experiment/rq2/manual/ablation")
    output_base_dir = os.path.join(project_dir, "Codes/Experiment/major/review-d/ablcation_prompts/results")
    common_words_file = os.path.join(project_dir, "archive/words.txt")
    entity_rules_file = os.path.join(project_dir, "Codes/GPTAnalysis/EntityRules/entity-1")
    
    # 加载常用词
    common_words = load_common_words(common_words_file)
    
    # 加载实体定义
    entity_definitions = read_file(entity_rules_file)
    
    # 设置正则表达式用于提取包名
    regex = r"(?:@[a-zA-Z0-9\-]+\/)?[a-zA-Z0-9][a-zA-Z0-9\._\-]+"
    
    # 加载所有版本的提示词
    version_prompts = load_prompt_versions(prompts_dir)
    safe_print(f"已加载 {len(version_prompts)} 个版本的提示词")
    
    # 获取需要处理的文件列表
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    safe_print(f"找到 {len(txt_files)} 个需要处理的文件")
    
    # 检查已处理文件
    processed_files = set()
    for version in version_prompts:
        version_dir = os.path.join(output_base_dir, version)
        if os.path.exists(version_dir):
            json_files = [f for f in os.listdir(version_dir) if f.endswith('.json')]
            # 对于单步骤版本，直接检查文件名
            base_names = set()
            for json_file in json_files:
                if '_extract.json' not in json_file and '_relation.json' not in json_file and '_verify.json' not in json_file:
                    base_name = os.path.splitext(json_file)[0] + '.txt'
                    base_names.add(base_name)
            
            # 对于三步骤版本，检查是否所有步骤都完成
            for json_file in json_files:
                if '_verify.json' in json_file:
                    base_name = json_file.replace('_verify.json', '.txt')
                    extract_file = json_file.replace('_verify.json', '_extract.json')
                    relation_file = json_file.replace('_verify.json', '_relation.json')
                    
                    if (os.path.exists(os.path.join(version_dir, extract_file)) and 
                        os.path.exists(os.path.join(version_dir, relation_file))):
                        base_names.add(base_name)
            
            processed_files.update(base_names)
    
    safe_print(f"已处理 {len(processed_files)} 个文件")
    
    # 过滤掉已处理的文件
    txt_files = [f for f in txt_files if f not in processed_files]
    safe_print(f"剩余 {len(txt_files)} 个文件需要处理")
    
    # 准备任务数据
    tasks = []
    for txt_file in txt_files:
        file_path = os.path.join(input_dir, txt_file)
        task_data = (
            file_path, txt_file, version_prompts, 
            output_base_dir, common_words, regex, entity_definitions
        )
        tasks.append(task_data)
    
    if not tasks:
        safe_print("没有需要处理的文件")
        return
    
    # 计算进程数量
    num_processes = min(24, len(tasks))  # 最多24个进程，但不超过任务数量
    
    safe_print(f"启动 {num_processes} 个进程处理 {len(tasks)} 个文件")
    
    # 使用进程池并行处理
    ctx = multiprocessing.get_context('spawn')
    with ctx.Pool(processes=num_processes) as pool:
        results = list(tqdm(
            pool.imap(process_file_task, tasks),
            total=len(tasks),
            desc="处理文件"
        ))
    
    # 输出处理结果
    successful = [r for r in results if r is not None]
    failed = len(tasks) - len(successful)
    safe_print(f"处理完成。成功: {len(successful)}, 失败: {failed}")

if __name__ == "__main__":
    main() 