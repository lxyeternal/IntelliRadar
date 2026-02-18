# !/usr/bin/env python
# -*- coding:utf-8 -*-

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

print_lock = Lock()


def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)


def process_file_task(task_data):
    """
    Process a single file in an independent process.
    Receives only serializable data to avoid pickle issues with class instances.
    """
    (output_base_dir, file_path, file_name, source,
     api_key, entity, prompts, common_words, regex, max_attempts, host,
     models, prompt_types) = task_data

    openai_client = openai.OpenAI(api_key=api_key)

    try:
        safe_print(f"[Process {os.getpid()}] Starting processing: {source}/{file_name}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

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

        for model, model_type in models.items():
            safe_print(f"[Process {os.getpid()}] {file_name} - Using model {model}")
            for prompt_type in prompt_types:
                extract_prompt = get_prompt_from_dict(prompts, prompt_type, "extract")
                extract_result = entity_extract_llm(content, filtered_words, model, extract_prompt,
                                                    entity, openai_client, max_attempts, model_type, host)
                extract_path = get_output_path(output_base_dir, model, prompt_type, file_name, "extract")
                save_json(extract_result, extract_path)
                safe_print(f"[Process {os.getpid()}] {file_name} - Model {model} - Entity extraction completed")

                relation_prompt = get_prompt_from_dict(prompts, prompt_type, "relation")
                relation_result = entity_relation_llm(content, extract_result, model, relation_prompt,
                                                      openai_client, max_attempts, model_type, host)
                relation_path = get_output_path(output_base_dir, model, prompt_type, file_name, "relation")
                save_json(relation_result, relation_path)
                safe_print(f"[Process {os.getpid()}] {file_name} - Model {model} - Entity relationship completed")

                verify_prompt = get_prompt_from_dict(prompts, prompt_type, "verify")
                verify_result = info_verify_llm(content, relation_result, model, verify_prompt,
                                                openai_client, max_attempts, model_type, host)
                verify_path = get_output_path(output_base_dir, model, prompt_type, file_name, "verify")
                save_json(verify_result, verify_path)
                safe_print(f"[Process {os.getpid()}] {file_name} - Model {model} - Information verification completed")

        safe_print(f"[Process {os.getpid()}] Processing completed: {source}/{file_name}")
        return f"{source}/{file_name}"
    except Exception as e:
        safe_print(f"[Process {os.getpid()}] Error processing {source}/{file_name}: {str(e)}")
        return None


def get_prompt_from_dict(prompts, prompt_type, step):
    if prompt_type == "default":
        if step == "extract":
            return prompts["entityextract"]
        elif step == "relation":
            return prompts["entityrelation"]
        else:
            return prompts["infoverify"]
    elif prompt_type == "cot":
        if step == "extract":
            return prompts["entityextract_cot"]
        elif step == "relation":
            return prompts["entityrelation_cot"]
        else:
            return prompts["infoverify_cot"]
    else:
        if step == "extract":
            return prompts["entityextract_cot_fewshot"]
        elif step == "relation":
            return prompts["entityrelation_cot_fewshot"]
        else:
            return prompts["infoverify_cot_fewshot"]


def get_output_path(base_dir, model, prompt_type, file_name, step):
    output_dir = os.path.join(base_dir, model, prompt_type)
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(file_name)[0]
    output_file = f"{base_name}_{model}_{step}_{prompt_type}.json"
    return os.path.join(output_dir, output_file)


def save_json(data, file_name):
    folder = os.path.dirname(file_name)
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(data)


def num_tokens_from_messages(content, model="gpt-3.5-turbo-16k-0613"):
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    num_tokens = len(encoding.encode(content))
    return num_tokens


def token_slice(content):
    """Slice content to fit within the token limit, returning the first segment."""
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
    if model_type == "azure":
        return azure_query(model, message_text, max_tokens, openai_client, max_attempts)
    else:
        return ollama_query(model, message_text, max_tokens, host, max_attempts)


def azure_query(model, message_text, max_tokens, openai_client, max_attempts):
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
            "top_p": 0.3,
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
    token_length = num_tokens_from_messages(content)
    safe_print(f"[Process {os.getpid()}] Token length: {token_length}")
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
        self.models = {
            "llama3.1:70b": "ollama",
            "llama3.3:70b": "ollama",
            "qwen2.5:72b": "ollama"
        }

        self.prompt_types = [
            "cot"
        ]

        self.steps = [
            "extract",
            "relation",
            "verify"
        ]

        current_dir = os.path.dirname(__file__)
        codes_dir = os.path.dirname(current_dir)
        project_dir = os.path.dirname(codes_dir)

        current_dir = "/Users/blue/Documents/Github/SCC_Intelligence/Codes/GPTAnalysis"
        codes_dir = "/Users/blue/Documents/Github/SCC_Intelligence/Codes"
        project_dir = "/Users/blue/Documents/Github/SCC_Intelligence"

        self.json_dir = os.path.join(project_dir, "Dataset", "NewJson")
        self.content_dir = os.path.join(project_dir, "Dataset", "NewContent")
        self.common_words_file = os.path.join(project_dir, "archive", "words.txt")
        self.entity_file = os.path.join(codes_dir, 'GPTAnalysis', 'EntityRules', 'entity-1')

        prompts_dir = os.path.join(codes_dir, 'GPTAnalysis', 'Prompts')
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

        self.config_path = os.path.join(project_dir, "Configs", "config.json")
        with open(self.config_path, 'r') as file:
            self.config = json.load(file)

        self.oclient = AzureOpenAI(
            api_key=self.config["azure_api_key"],
            api_version=self.config["azure_api_version"],
            azure_endpoint=self.config["azure_api_base"]
        )

        self.openai_client = openai.OpenAI(
            api_key = "sk-proj-yyNv63ETnZNQL6F3ptX4Ht2_U2u9hKegXNNDtHnUAo9LumE8FJhM4Ts5mSMgP8A"
        )

        self.host = "127.0.0.1"
        self.load_common_words()

    def read_file(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def load_common_words(self):
        with open(self.common_words_file, 'r', encoding='utf-8') as file:
            for line in file:
                self.common_words.add(line.strip().lower())

    def get_processed_files(self, output_dir: str, source: str) -> set:
        """Get the set of files already fully processed across all models for a given source."""
        processed_files = set()
        for model in self.models:
            source_dir = os.path.join(output_dir, source, model, "cot")

            if not os.path.exists(source_dir):
                continue

            for filename in os.listdir(source_dir):
                if filename.endswith(f"_{model}_verify_cot.json"):
                    original_name = filename.replace(f"_{model}_verify_cot.json", "")
                    processed_files.add(original_name + '.txt')

        # Only keep files that have been processed by ALL models
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
        """Process all files in a source directory using multiprocessing."""
        source_dir = os.path.join(dataset_path, source)
        if not os.path.isdir(source_dir):
            return

        output_source_dir = os.path.join(output_base_dir, source)
        os.makedirs(output_source_dir, exist_ok=True)

        for model in self.models:
            model_dir = os.path.join(output_source_dir, model, "cot")
            os.makedirs(model_dir, exist_ok=True)

        processed_files = self.get_processed_files(output_base_dir, source)
        safe_print(f"Found {len(processed_files)} already processed files in {source}")

        file_tasks = []
        txt_files = [f for f in os.listdir(source_dir) if f.endswith('.txt')]
        for txt_file in txt_files:
            if txt_file in processed_files:
                safe_print(f"Skipping {txt_file} in source {source} - already processed")
                continue

            file_path = os.path.join(source_dir, txt_file)

            task_data = (
                output_source_dir,
                file_path,
                txt_file,
                source,
                "sk-proj-yyNv63ETnZNQL6F3pfFgJNNDtHnUAo9LumE8FJhM4Ts5mSMgP8A",
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

        num_processes = min(24, len(file_tasks))

        safe_print(f"Starting {num_processes} processes to handle {len(file_tasks)} files in {source}")

        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(processes=num_processes) as pool:
            results = list(tqdm(
                pool.imap(process_file_task, file_tasks),
                total=len(file_tasks),
                desc=f"Processing {source}"
            ))

        successful = [r for r in results if r is not None]
        failed = len(file_tasks) - len(successful)
        safe_print(f"Source {source} processing completed. Success: {len(successful)}, Failed: {failed}")


if __name__ == '__main__':
    try:
        multiprocessing.set_start_method('spawn')
    except RuntimeError:
        pass

    ltmgpt = LTMGPT()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    codes_dir = os.path.dirname(current_dir)
    project_dir = os.path.dirname(codes_dir)

    dataset_path = os.path.join(project_dir, "Dataset", "NewContent")
    output_base_dir = os.path.join(project_dir, "Dataset", "NewJson")

    sources = ['recent_webpage']
    # sources = os.listdir(dataset_path)
    # sources = ['jfrog', 'securityaffairs', 'socket', 'reversinglabs', 'securityweek', 'checkpoint', 'rhisac',
    #            'fortinet', 'cybersecuritynews', 'thehackernews', 'tuxcare']

    for source in sources:
        ltmgpt.process_source_multiprocessing(source, dataset_path, output_base_dir)
