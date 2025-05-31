# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @File     : local_llm
# @Project  : SCC_Intelligence
# Time      : 12/28/24 13:43
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
from openai import AzureOpenAI
from nltk.corpus import stopwords
from typing import Dict, List

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))


class LTMGPT:
    def __init__(self):
        self.models = {
            # "llama3.3:70b-128k": "ollama",
            # "llama3.1:70b-128k": "ollama",
            # "qwen2.5:72b-128k": "ollama",
            # "csl-malicious-4o-mini": "azure",
            "gpt-4o": "azure"
        }

        self.prompt_types = [
            # "default",  # no cot
            # "cot",  # with cot
            "cot_fewshot"  # with cot and fewshot
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

        # current_dir = "/home/wenbo/SCC_Intelligence/Codes/GPTAnalysis"
        # codes_dir = "/home/wenbo/SCC_Intelligence/Codes"
        # project_dir = "/home/wenbo/SCC_Intelligence"

        # Initialize base directories
        self.json_dir = os.path.join(project_dir, "Dataset", "Json")
        self.content_dir = os.path.join(project_dir, "Dataset", "Content")
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

    def extract_package_names(self, content: str) -> set:
        """Extract package names using regex pattern."""
        try:
            unique_words = list()
            matches = re.findall(self.regex, content)
            unique_matches = set(matches)
            for word in unique_matches:
                if word.endswith(".") or word.endswith(","):
                    word = word[:-1]
                    if word.lower() not in self.common_words:
                        unique_words.append(word)
                else:
                    if word.lower() not in self.common_words:
                        unique_words.append(word)
            return set(unique_words)
        except Exception as e:
            print(f"Error extracting package names: {e}")
            return set()

    @staticmethod
    def read_txt(file_name: str) -> str:
        """Read and return text file contents."""
        with open(file_name, "r", encoding="utf-8") as f:
            content = f.read()
        return content

    @staticmethod
    def save_json(data: str, file_name: str):
        """Save data to JSON file, creating directories if needed."""
        folder = os.path.dirname(file_name)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(data)

    def num_tokens_from_messages(self, content: str, model: str = "gpt-3.5-turbo-16k-0613") -> int:
        """Calculate the number of tokens in the content."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")

        if model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
        }:
            num_tokens = len(encoding.encode(content))
            return num_tokens
        elif model == "gpt-3.5-turbo-0301":
            num_tokens = len(encoding.encode(content))
            return num_tokens
        elif "gpt-3.5-turbo" in model:
            print("Warning: gpt-3.5-turbo may update over time. Using gpt-3.5-turbo-0613 token count.")
            return self.num_tokens_from_messages(content, model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            print("Warning: gpt-4 may update over time. Using gpt-4-0613 token count.")
            return self.num_tokens_from_messages(content, model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"num_tokens_from_messages() is not implemented for model {model}."
            )

    def token_slice(self, content: str) -> str:
        """Slice content to fit within token limits."""
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

        return decode_segments[0]

    def get_prompt(self, step: str, prompt_type: str) -> str:
        """Get the appropriate prompt based on step and type."""
        if prompt_type == "default":
            if step == "extract":
                return self.prompts["entityextract"]
            elif step == "relation":
                return self.prompts["entityrelation"]
            else:  # verify
                return self.prompts["infoverify"]
        elif prompt_type == "cot":
            if step == "extract":
                return self.prompts["entityextract_cot"]
            elif step == "relation":
                return self.prompts["entityrelation_cot"]
            else:  # verify
                return self.prompts["infoverify_cot"]
        else:  # cot_fewshot
            if step == "extract":
                return self.prompts["entityextract_cot_fewshot"]
            elif step == "relation":
                return self.prompts["entityrelation_cot_fewshot"]
            else:  # verify
                return self.prompts["infoverify_cot_fewshot"]

    def get_output_path(self, base_dir: str, model: str, prompt_type: str, file_name: str, step: str) -> str:
        """Generate output path for results."""
        output_dir = os.path.join(base_dir, model, prompt_type)
        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.splitext(file_name)[0]
        output_file = f"{base_name}_{model}_{step}_{prompt_type}.json"
        return os.path.join(output_dir, output_file)

    def perform_query(self, model: str, message_text: List[Dict], max_tokens: int) -> str:
        """Perform query based on model type."""
        if self.models[model] == "azure":
            return self.azure_query(model, message_text, max_tokens)
        else:  # ollama
            return self.ollama_query(model, message_text, max_tokens)

    def azure_query(self, model: str, message_text: List[Dict], max_tokens: int) -> str:
        """Perform query using Azure OpenAI."""
        max_tokens = 16000
        wait_time = 10
        attempt = 0
        while attempt < self.max_attempts:
            try:
                completion = self.oclient.chat.completions.create(
                    model=model,
                    messages=message_text,
                    response_format={"type": "json_object"},
                    temperature=0,
                    max_tokens=max_tokens,
                    top_p=0.3,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                    stream=False
                )
                return completion.choices[0].message.content
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {model}: {e}")
                attempt += 1
                time.sleep(wait_time)
                wait_time += 5
        return ""

    def ollama_query(self, model: str, message_text: List[Dict], max_tokens: int) -> str:
        """Perform query using Ollama."""
        max_tokens = 32000
        wait_time = 10
        attempt = 0
        url = f"http://{self.host}:11434/api/chat"

        payload = {
            "model": model,
            "stream": False,
            "messages": message_text
        }

        while attempt < self.max_attempts:
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(payload)
                )
                return response.json()['message']['content']
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {model}: {e}")
                attempt += 1
                time.sleep(wait_time)
                wait_time += 5
        return ""

    def process_content(self, output_base_dir: str, file_path: str, file_name: str):
        """Process content through all models, prompt types and steps."""
        content = self.read_txt(file_path)
        re_pkgnames = self.extract_package_names(content)
        filtered_words = [word for word in re_pkgnames if word not in stop_words]

        # For each model
        for model in self.models:
            print(f"Processing with model: {model}")
            # For each prompt type
            for prompt_type in self.prompt_types:
                print(f"Using prompt type: {prompt_type}")

                # Step 1: Entity Extraction
                extract_prompt = self.get_prompt("extract", prompt_type)
                extract_result = self.entity_extract_llm(content, filtered_words, model, extract_prompt)
                extract_path = self.get_output_path(output_base_dir, model, prompt_type, file_name, "extract")
                self.save_json(extract_result, extract_path)

                # Step 2: Entity Relation
                relation_prompt = self.get_prompt("relation", prompt_type)
                relation_result = self.entity_realtion_llm(content, extract_result, model, relation_prompt)
                relation_path = self.get_output_path(output_base_dir, model, prompt_type, file_name, "relation")
                self.save_json(relation_result, relation_path)

                # Step 3: Information Verification
                verify_prompt = self.get_prompt("verify", prompt_type)
                verify_result = self.info_verify_llm(content, relation_result, model, verify_prompt)
                verify_path = self.get_output_path(output_base_dir, model, prompt_type, file_name, "verify")
                self.save_json(verify_result, verify_path)

    def count_total_tokens(self, messages: list) -> int:
        total_tokens = 0
        for message in messages:
            for value in message.values():
                if isinstance(value, str):
                    tokens = self.num_tokens_from_messages(value)
                    total_tokens += tokens
        num_messages = len(messages)
        total_tokens += 4 * num_messages
        total_tokens += 2
        return total_tokens

    def entity_extract_llm(self, content: str, potential_entity: List[str], model: str, prompt: str) -> str:
        token_length = self.num_tokens_from_messages(content)
        print(f"Token length: {token_length}")
        max_tokens = 110000 - int(1.0 * token_length)
        if token_length > 110000:
            content = self.token_slice(content)
        message_text = [
            {"role": "system",
             "content": "You are a cybersecurity expert specializing in analyzing malicious packages in package managers. Your task is to extract specific entity information from the given text, focusing only on the entities defined in the entity description."},
            {"role": "user", "content": f"""
                    === SOURCE CONTENT ===
                    {content}

                    === POTENTIAL MALICIOUS PACKAGES ===
                    {str(potential_entity)}

                    === ENTITY DEFINITIONS ===
                    {self.entity}

                    === EXTRACTION INSTRUCTIONS ===
                    {prompt}
                    """}
        ]
        return self.perform_query(model, message_text, max_tokens)

    def entity_realtion_llm(self, content: str, extracted_entity: str, model: str, prompt: str) -> str:
        token_length = self.num_tokens_from_messages(content)
        max_tokens = 110000 - int(1.0 * token_length)
        if token_length > 110000:
            content = self.token_slice(content)
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
        return self.perform_query(model, message_text, max_tokens)

    def info_verify_llm(self, content: str, entity_relation: str, model: str, prompt: str) -> str:
        token_length = self.num_tokens_from_messages(content)
        max_tokens = 110000 - int(1.0 * token_length)
        if token_length > 110000:
            content = self.token_slice(content)
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
        return self.perform_query(model, message_text, max_tokens)


if __name__ == '__main__':
    ltmgpt = LTMGPT()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    codes_dir = os.path.dirname(current_dir)
    project_dir = os.path.dirname(codes_dir)

    dataset_path = os.path.join(codes_dir, "Experiment", "rq2", "manual", "ablation")
    output_base_dir = os.path.join(codes_dir, "Experiment", "rq2", "manual", "localllm")

    intell_files = os.listdir(dataset_path)
    for intell_file in intell_files:
        print(f"Processing file: {intell_file}")
        file_path = os.path.join(dataset_path, intell_file)
        ltmgpt.process_content(output_base_dir, file_path, intell_file)
