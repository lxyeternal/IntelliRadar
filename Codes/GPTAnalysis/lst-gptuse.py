# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : local_llm
# @Project  : SCC_Intelligence
# Time      : 12/28/24 13:43
# Author    : blue
# version   : python
# Description：
"""

# !/usr/bin/env python
# -*-coding:utf-8 -*-

import re
import os
import json
import time
import nltk
import requests
import tiktoken
import openai
import multiprocessing
from multiprocessing import Pool, Lock
from openai import AzureOpenAI
from nltk.corpus import stopwords
from typing import Dict, List
from tqdm import tqdm
from functools import partial

nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

# 创建一个全局锁，用于安全打印
print_lock = Lock()

def safe_print(*args, **kwargs):
    """线程安全的打印函数"""
    with print_lock:
        print(*args, **kwargs)

def process_file_task(task_data):
    """
    独立函数处理单个文件，避免pickle问题
    只接收必要的数据而不是整个类实例
    """
    (output_base_dir, file_path, file_name, source, 
     api_key, entity, prompts, common_words, regex, max_attempts, host, 
     models, prompt_types) = task_data
    
    # 创建新的OpenAI客户端
    openai_client = openai.OpenAI(api_key=api_key)
    
    try:
        safe_print(f"[进程 {os.getpid()}] 开始处理: {source}/{file_name}")
        
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 提取包名
        unique_words = []
        try:
            matches = re.findall(regex, content)
            unique_matches = set(matches)
            for word in unique_matches:
                if word.endswith(".") or word.endswith(","):
                    word = word[:-1]
                    if word.lower() not in common_words:
                        unique_words.append(word)
                else:
                    if word.lower() not in common_words:
                        unique_words.append(word)
            re_pkgnames = set(unique_words)
        except Exception as e:
            safe_print(f"Error extracting package names: {e}")
            re_pkgnames = set()
        
        filtered_words = [word for word in re_pkgnames if word not in stop_words]
        
        # 为每个模型处理
        for model, model_type in models.items():
            safe_print(f"[进程 {os.getpid()}] {file_name} - 使用模型 {model}")
            # 为每个提示类型处理
            for prompt_type in prompt_types:
                # 步骤1: 实体提取
                extract_prompt = get_prompt_from_dict(prompts, prompt_type, "extract")
                extract_result = entity_extract_llm(content, filtered_words, model, extract_prompt, 
                                                  entity, openai_client, max_attempts, model_type, host)
                extract_path = get_output_path(output_base_dir, model, prompt_type, file_name, "extract")
                save_json(extract_result, extract_path)
                safe_print(f"[进程 {os.getpid()}] {file_name} - 模型 {model} - 完成实体提取")

                # 步骤2: 实体关系
                relation_prompt = get_prompt_from_dict(prompts, prompt_type, "relation")
                relation_result = entity_relation_llm(content, extract_result, model, relation_prompt, 
                                                    openai_client, max_attempts, model_type, host)
                relation_path = get_output_path(output_base_dir, model, prompt_type, file_name, "relation")
                save_json(relation_result, relation_path)
                safe_print(f"[进程 {os.getpid()}] {file_name} - 模型 {model} - 完成实体关系")

                # 步骤3: 信息验证
                verify_prompt = get_prompt_from_dict(prompts, prompt_type, "verify")
                verify_result = info_verify_llm(content, relation_result, model, verify_prompt, 
                                              openai_client, max_attempts, model_type, host)
                verify_path = get_output_path(output_base_dir, model, prompt_type, file_name, "verify")
                save_json(verify_result, verify_path)
                safe_print(f"[进程 {os.getpid()}] {file_name} - 模型 {model} - 完成信息验证")
        
        safe_print(f"[进程 {os.getpid()}] 完成处理: {source}/{file_name}")
        return f"{source}/{file_name}"
    except Exception as e:
        safe_print(f"[进程 {os.getpid()}] 处理 {source}/{file_name} 时出错: {str(e)}")
        return None

def get_prompt_from_dict(prompts, prompt_type, step):
    """从提示字典中获取适当的提示"""
    if prompt_type == "default":
        if step == "extract":
            return prompts["entityextract"]
        elif step == "relation":
            return prompts["entityrelation"]
        else:  # verify
            return prompts["infoverify"]
    elif prompt_type == "cot":
        if step == "extract":
            return prompts["entityextract_cot"]
        elif step == "relation":
            return prompts["entityrelation_cot"]
        else:  # verify
            return prompts["infoverify_cot"]
    else:  # cot_fewshot
        if step == "extract":
            return prompts["entityextract_cot_fewshot"]
        elif step == "relation":
            return prompts["entityrelation_cot_fewshot"]
        else:  # verify
            return prompts["infoverify_cot_fewshot"]

def get_output_path(base_dir, model, prompt_type, file_name, step):
    """生成结果输出路径"""
    # 创建目录结构
    output_dir = os.path.join(base_dir, model, prompt_type)
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名
    base_name = os.path.splitext(file_name)[0]
    output_file = f"{base_name}_{model}_{step}_{prompt_type}.json"
    return os.path.join(output_dir, output_file)

def save_json(data, file_name):
    """保存数据到JSON文件"""
    folder = os.path.dirname(file_name)
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(data)

def num_tokens_from_messages(content, model="gpt-3.5-turbo-16k-0613"):
    """计算内容中的token数量"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    num_tokens = len(encoding.encode(content))
    return num_tokens

def token_slice(content):
    """将内容切片以适应token限制"""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-16k-0613")
    content_tokens = encoding.encode(content)
    token_limit = 30000
    segments = []
    current_segment = []
    current_length = 0
    decode_segments = []

    for token in content_tokens:
        if current_length + 1 > token_limit:
            segments.append(current_segment)
            current_segment = [token]
            current_length = 1
        else:
            current_segment.append(token)
            current_length += 1

    if current_segment:
        segments.append(current_segment)

    for segment in segments:
        segment_text = encoding.decode(segment)
        decode_segments.append(segment_text)

    return decode_segments[0] if decode_segments else ""

def perform_query(model, message_text, max_tokens, openai_client, max_attempts, model_type, host):
    """执行查询"""
    if model_type == "azure":
        return azure_query(model, message_text, max_tokens, openai_client, max_attempts)
    else:  # ollama
        return ollama_query(model, message_text, max_tokens, host, max_attempts)

def azure_query(model, message_text, max_tokens, openai_client, max_attempts):
    """使用Azure OpenAI执行查询"""
    max_tokens = 16000
    wait_time = 10
    attempt = 0
    while attempt < max_attempts:
        try:
            completion = openai_client.chat.completions.create(
                model=model,
                messages=message_text,
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=max_tokens,
                top_p=0.3,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False,
                seed=42
            )
            return completion.choices[0].message.content
        except Exception as e:
            safe_print(f"Attempt {attempt + 1} failed for {model}: {e}")
            attempt += 1
            time.sleep(wait_time)
            wait_time += 5
    return ""

    
def ollama_query(model, message_text, max_tokens, host, max_attempts):
    """使用Ollama执行查询"""
    max_tokens = 32000
    wait_time = 10
    attempt = 0
    url = f"http://127.0.0.1:11434/api/chat"
        
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": message_text,
        "options": {
            "temperature": 0,
            "seed": 42,
            "num_ctx": 65536
        },
    }

    while attempt < max_attempts:
        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload)
            )
            print(response.json())
            return response.json()['message']['content']
        except Exception as e:
            safe_print(f"Attempt {attempt + 1} failed for {model}: {e}")
            attempt += 1
            time.sleep(wait_time)
            wait_time += 5
    return ""

def entity_extract_llm(content, potential_entity, model, prompt, entity, openai_client, max_attempts, model_type, host):
    """实体提取"""
    token_length = num_tokens_from_messages(content)
    safe_print(f"[进程 {os.getpid()}] Token length: {token_length}")
    max_tokens = 110000 - int(1.0 * token_length)
    if token_length > 110000:
        content = token_slice(content)
    message_text = [
        {"role": "system",
         "content": "You are a cybersecurity expert specializing in analyzing malicious packages in package managers. Your task is to extract specific entity information from the given text, focusing only on the entities defined in the entity description."},
        {"role": "user", "content": f"""
                === SOURCE CONTENT ===
                {content}

                === POTENTIAL MALICIOUS PACKAGES ===
                {str(potential_entity)}

                === ENTITY DEFINITIONS ===
                {entity}

                === EXTRACTION INSTRUCTIONS ===
                {prompt}
                """}
    ]
    return perform_query(model, message_text, max_tokens, openai_client, max_attempts, model_type, host)

def entity_relation_llm(content, extracted_entity, model, prompt, openai_client, max_attempts, model_type, host):
    """实体关系分析"""
    token_length = num_tokens_from_messages(content)
    max_tokens = 110000 - int(1.0 * token_length)
    if token_length > 110000:
        content = token_slice(content)
    message_text = [
        {"role": "system",
         "content": "You are a cybersecurity expert specializing in analyzing relationships between entities in malicious package reports. Your task is to analyze the relationships between the extracted entities by referring to the original content, and organize them into package-centric JSON objects."},
        {"role": "user", "content": f"""
            === SOURCE CONTENT ===
            {content}

            === EXTRACTED ENTITIES ===
            {extracted_entity}

            === RELATIONSHIP ANALYSIS INSTRUCTIONS ===
            {prompt}
            """}
    ]
    return perform_query(model, message_text, max_tokens, openai_client, max_attempts, model_type, host)

def info_verify_llm(content, entity_relation, model, prompt, openai_client, max_attempts, model_type, host):
    """信息验证"""
    token_length = num_tokens_from_messages(content)
    max_tokens = 110000 - int(1.0 * token_length)
    if token_length > 110000:
        content = token_slice(content)
    message_text = [
        {"role": "system",
         "content": "You are a cybersecurity expert specializing in verifying the accuracy of extracted information about malicious packages in package managers. Your task is to cross-check the extracted entities and their relationships against the original content, ensuring all information is accurate and supported by the text."},
        {"role": "user", "content": f"""
            === SOURCE CONTENT ===
            {content}

            === EXTRACTED ENTITIES AND RELATIONS ===
            {entity_relation}

            === VERIFICATION INSTRUCTIONS ===
            {prompt}
            """}
    ]
    return perform_query(model, message_text, max_tokens, openai_client, max_attempts, model_type, host)

class LTMGPT:
    def __init__(self):
        # 使用三个Ollama模型
        self.models = {
            "llama3.1:70b": "ollama",
            "llama3.3:70b": "ollama",
            "qwen2.5:72b": "ollama"
        }

        self.prompt_types = [
            "cot"  # with cot and fewshot
        ]

        self.steps = [
            "extract",
            "relation",
            "verify"
        ]

        # Setup paths
        current_dir = os.path.dirname(__file__)
        codes_dir = os.path.dirname(current_dir)
        project_dir = os.path.dirname(codes_dir)

        current_dir = "/Users/blue/Documents/Github/SCC_Intelligence/Codes/GPTAnalysis"
        codes_dir = "/Users/blue/Documents/Github/SCC_Intelligence/Codes"
        project_dir = "/Users/blue/Documents/Github/SCC_Intelligence"

        # Initialize base directories
        self.json_dir = os.path.join(project_dir, "Dataset", "NewJson")
        self.content_dir = os.path.join(project_dir, "Dataset", "NewContent")
        self.common_words_file = os.path.join(project_dir, "archive", "words.txt")
        self.entity_file = os.path.join(codes_dir, 'GPTAnalysis', 'EntityRules', 'entity-1')

        # Load prompts
        prompts_dir = os.path.join(codes_dir, 'GPTAnalysis', 'LtM_prompts')
        self.prompts = {
            "entityextract_cot_fewshot": self.read_file(os.path.join(prompts_dir, 'entityextract_cot_fewshot')),
            "entityrelation_cot_fewshot": self.read_file(os.path.join(prompts_dir, 'entityrelation_cot_fewshot')),
            "infoverify_cot_fewshot": self.read_file(os.path.join(prompts_dir, 'infoverify_cot_fewshot')),
            "entityextract_cot": self.read_file(os.path.join(prompts_dir, 'entityextract_cot')),
            "entityrelation_cot": self.read_file(os.path.join(prompts_dir, 'entityrelation_cot')),
            "infoverify_cot": self.read_file(os.path.join(prompts_dir, 'infoverify_cot')),
            "entityextract": self.read_file(os.path.join(prompts_dir, 'entityextract')),
            "entityrelation": self.read_file(os.path.join(prompts_dir, 'entityrelation')),
            "infoverify": self.read_file(os.path.join(prompts_dir, 'infoverify'))
        }

        self.entity = self.read_file(self.entity_file)
        self.common_words = set()
        self.dealt_pkgs = list()
        self.regex = r"(?:@[a-zA-Z0-9\-]+\/)?[a-zA-Z0-9][a-zA-Z0-9\._\-]+"
        self.max_attempts = 5

        # Load config
        self.config_path = os.path.join(project_dir, "Configs", "config.json")
        with open(self.config_path, 'r') as file:
            self.config = json.load(file)

        # Initialize Azure client
        self.oclient = AzureOpenAI(
            api_key=self.config["azure_api_key"],
            api_version=self.config["azure_api_version"],
            azure_endpoint=self.config["azure_api_base"]
        )

        self.openai_client = openai.OpenAI(
            api_key = "sk-proj-yyNv63ETnZNQL6F3ptMWjBZFynya71kFEMxX4Ht2_U2u9hKegXNNDtHnUAo9LumE8FJhM4Ts5mSMgP8A"
        )

        self.host = "127.0.0.1"
        self.load_common_words()

    def read_file(self, file_path: str) -> str:
        """Read and return the contents of a file."""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def load_common_words(self):
        """Load common words from file into set."""
        with open(self.common_words_file, 'r', encoding='utf-8') as file:
            for line in file:
                self.common_words.add(line.strip().lower())

    def get_processed_files(self, output_dir: str, source: str) -> set:
        """
        获取指定source目录下已经处理完成的文件列表
        """
        processed_files = set()
        # 检查所有模型的输出目录
        for model in self.models:
            # 检查输出目录中的verify文件
            source_dir = os.path.join(output_dir, source, model, "cot")
            
            if not os.path.exists(source_dir):
                continue

            for filename in os.listdir(source_dir):
                # 只检查verify步骤的文件
                if filename.endswith(f"_{model}_verify_cot.json"):
                    # 从文件名中提取原始文件名
                    original_name = filename.replace(f"_{model}_verify_cot.json", "")
                    processed_files.add(original_name + '.txt')  # 加回.txt后缀
        
        # 只有当一个文件在所有模型中都已处理完成时，才视为已处理
        fully_processed = set()
        for file in processed_files:
            all_models_processed = True
            for model in self.models:
                model_dir = os.path.join(output_dir, source, model, "cot")
                if not os.path.exists(model_dir):
                    all_models_processed = False
                    break
                verify_file = os.path.splitext(file)[0] + f"_{model}_verify_cot.json"
                if not os.path.exists(os.path.join(model_dir, verify_file)):
                    all_models_processed = False
                    break
            
            if all_models_processed:
                fully_processed.add(file)
                
        return fully_processed

    def process_source_multiprocessing(self, source, dataset_path, output_base_dir):
        """使用多进程处理一个source目录下的所有文件"""
        source_dir = os.path.join(dataset_path, source)
        if not os.path.isdir(source_dir):
            return  # 跳过非文件夹
        
        # 确保输出目录存在
        output_source_dir = os.path.join(output_base_dir, source)
        os.makedirs(output_source_dir, exist_ok=True)
        
        # 为每个模型创建目录
        for model in self.models:
            model_dir = os.path.join(output_source_dir, model, "cot")
            os.makedirs(model_dir, exist_ok=True)
        
        # 获取当前source目录下已经处理完成的文件
        processed_files = self.get_processed_files(output_base_dir, source)
        safe_print(f"Found {len(processed_files)} already processed files in {source}")
        
        # 收集需要处理的文件
        file_tasks = []
        txt_files = [f for f in os.listdir(source_dir) if f.endswith('.txt')]
        for txt_file in txt_files:
            # 检查文件是否已经处理过
            if txt_file in processed_files:
                safe_print(f"Skipping {txt_file} in source {source} - already processed")
                continue
            
            file_path = os.path.join(source_dir, txt_file)
            
            # 只传递需要的数据，不传递整个类实例
            task_data = (
                output_source_dir, 
                file_path, 
                txt_file, 
                source,
                "sk-proj-yyNv63ETnZNQL6F3pfFgJTbdieNlBb8-IwvyXNNDtHnUAo9LumE8FJhM4Ts5mSMgP8A",
                self.entity,
                self.prompts,
                self.common_words,
                self.regex,
                self.max_attempts,
                self.host,
                self.models,
                self.prompt_types
            )
            file_tasks.append(task_data)
        
        if not file_tasks:
            safe_print(f"No files to process in {source}")
            return
        
        # 计算需要使用的进程数量
        num_processes = min(24, len(file_tasks))  # 最多24个进程，但不超过任务数量
        
        safe_print(f"Starting {num_processes} processes to handle {len(file_tasks)} files in {source}")
        
        # 使用进程池并行处理，确保使用spawn方法创建进程
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(processes=num_processes) as pool:
            # 使用map代替starmap，每个任务只传一个参数
            results = list(tqdm(
                pool.imap(process_file_task, file_tasks), 
                total=len(file_tasks), 
                desc=f"处理 {source}"
            ))
        
        # 输出处理结果
        successful = [r for r in results if r is not None]
        failed = len(file_tasks) - len(successful)
        safe_print(f"Source {source} processing completed. Success: {len(successful)}, Failed: {failed}")


if __name__ == '__main__':
    # 安全地设置多进程启动方法
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        # 如果启动方法已设置，则跳过
        pass
    
    ltmgpt = LTMGPT()
    
    # 使用相对路径，从当前文件所在目录推导出 project_dir
    current_dir = os.path.dirname(os.path.abspath(__file__))
    codes_dir = os.path.dirname(current_dir)
    project_dir = os.path.dirname(codes_dir)
    
    # 动态构造输入和输出路径
    dataset_path = os.path.join(project_dir, "Dataset", "NewContent")
    output_base_dir = os.path.join(project_dir, "Dataset", "NewJson")
    
    # 要处理的源文件夹
    sources = ['recent_webpage']
    # 如果需要处理所有源
    # sources = os.listdir(dataset_path)
    # sources = ['jfrog', 'securityaffairs', 'socket', 'reversinglabs', 'securityweek', 'checkpoint', 'rhisac',
    #            'fortinet', 'cybersecuritynews', 'thehackernews', 'tuxcare']
    
    # 对每个源使用多进程处理
    for source in sources:
        ltmgpt.process_source_multiprocessing(source, dataset_path, output_base_dir)