# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : lst-gptuse.py
# @Project  : SCC_Intelligence
# Time      : 25/7/24 7:53 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""


import re
import os
import json
import time
import nltk
import openai # 0.28.1
import tiktoken
# from openai import OpenAI
from nltk.corpus import stopwords
# 首次使用时需要下载停用词集
nltk.download('stopwords')
# 获取英语停用词集xw
stop_words = set(stopwords.words('english'))



class LTMGPT:
    def __init__(self):
        self.intell_source_dir = ""
        current_dir = os.path.dirname(__file__)
        codes_dir = os.path.dirname(current_dir)
        project_dir = os.path.dirname(codes_dir)
        self.json_dir = os.path.join(project_dir, "Dataset", "Json")
        self.content_dir = os.path.join(project_dir, "Dataset", "Content")
        self.common_words_file = os.path.join(project_dir, "archive", "words.txt")
        self.entity_file = os.path.join(codes_dir, 'GPTAnalysis/EntityRules/entity-1')
        self.entityrelation_prompt = self.read_file(os.path.join(codes_dir, 'GPTAnalysis/LtM_prompts/entityrelation'))
        self.entityextract_prompt = self.read_file(os.path.join(codes_dir, 'GPTAnalysis/LtM_prompts/entityextract'))
        self.infoverify_prompt = self.read_file(os.path.join(codes_dir, 'GPTAnalysis/LtM_prompts/infoverify'))
        self.entity = self.read_file(self.entity_file)
        self.common_words = set()
        self.dealt_pkgs = list()
        self.regex = r"(?:@[a-zA-Z0-9\-]+\/)?[a-zA-Z0-9][a-zA-Z0-9\._\-]+"
        self.max_attempts = 5  # 最大尝试次数
        self.config_path = os.path.join(project_dir, "Configs", "config.json")

        with open(self.config_path, 'r') as file:
            self.config = json.load(file)
        openai.api_type = self.config['azure_api_type']
        openai.api_base = self.config['azure_api_base']
        openai.api_version = self.config['azure_api_version']
        openai.api_key = self.config['azure_api_key']
        # self.openai_api_key = self.config['openai_api_key']
        # self.openai_client = OpenAI(api_key=self.openai_api_key)


    def read_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content


    def load_common_words(self):
        with open(self.common_words_file, 'r', encoding='utf-8') as file:
            for line in file:
                self.common_words.add(line.strip().lower())


    def load_dealt_pkgs(self):
        dealt_pkgs_dir = os.path.join(self.json_dir, self.intell_source_dir)
        if os.path.exists(dealt_pkgs_dir):
            self.dealt_pkgs = os.listdir(dealt_pkgs_dir)
            self.dealt_pkgs = [json_file.replace("_verify_gpt4.json", ".txt").replace("_relation_gpt4.json", ".txt").replace("_extract_gpt4.json", ".txt") for json_file in self.dealt_pkgs if json_file != ".DS_Store"]

    def extract_package_names(self, content):
        # PyPI 和 npm 的正则表达式
        try:
            unique_words = list()
            matches = re.findall(self.regex, content)
            # 去除重复的匹配项
            unique_matches = set(matches)
            for word in unique_matches:
                if word.endswith(".") or word.endswith(","):
                    word = word[:-1]
                    if word.lower() not in self.common_words:
                        unique_words.append(word)
                else:
                    if word.lower() not in self.common_words:
                        unique_words.append(word)
            unique_words = set(unique_words)
            return unique_words
        except Exception as e:
            print(f"An error occurred: {e}")
            return set()

    @staticmethod
    def read_txt(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            content = f.read()
        return content

    @staticmethod
    def save_json(data, file_name):
        # 获取文件夹路径
        folder = os.path.dirname(file_name)
        # 如果文件夹不存在，则创建它
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(data)

    def num_tokens_from_messages(self, content, model="gpt-3.5-turbo-16k-0613"):
        """Return the number of tokens used by a list of messages."""
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
            pass
        elif model == "gpt-3.5-turbo-0301":
            pass
        elif "gpt-3.5-turbo" in model:
            print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
            return self.num_tokens_from_messages(content, model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            return self.num_tokens_from_messages(content, model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
        num_tokens = len(encoding.encode(content))
        return num_tokens


    def token_slice(self, content):
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-16k-0613")
        content_tokens = encoding.encode(content)
        token_limit = 30000
        segments = []
        current_segment = []
        current_length = 0
        decode_segments = []
        for token in content_tokens:
            if current_length + 1 > token_limit:  # 达到或超过限制则开始新段
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

    def azure_query(self, message_text):
        max_tokens = 16000
        wait_time = 10
        attempt = 0
        output = ""
        while attempt < self.max_attempts:
            try:
                completion = openai.ChatCompletion.create(
                    # engine="csl-malicious",
                    engine="csl-malicious-4o-mini",
                    # engine="csl-malicious-35",
                    messages=message_text,
                    response_format={"type": "json_object"},
                    temperature=0,
                    max_tokens=max_tokens,
                    top_p=0.3,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None
                )
                output = completion.choices[0].message['content']
                break  # 如果成功，跳出循环
            except Exception as e:
                print(f"Attempt {attempt + 1}: An error occurred: {e}")
                attempt += 1
                time.sleep(wait_time)
                wait_time += 5  # 每次失败后增加等待时间
        print(output)
        return output


    def chatgpt_query(self, message_text):
        max_tokens = 16000
        wait_time = 10
        attempt = 0
        output = ""
        while attempt < self.max_attempts:
            try:
                completion = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=message_text,
                    temperature=0,
                    max_tokens=max_tokens,
                    top_p=0.3,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=None,
                    stream=False,
                )
                output = completion.choices[0].message.content
                break  # 如果成功，跳出循环
            except Exception as e:
                print(f"Attempt {attempt + 1}: An error occurred: {e}")
                attempt += 1
                time.sleep(wait_time)
                wait_time += 5  # 每次失败后增加等待时间
        print(output)
        return output

    def entity_extract_llm(self, content, potential_entity):
        # 统计 token 的数量
        token_length = self.num_tokens_from_messages(content)
        max_tokens = 110000 - int(1.0 * token_length)
        if token_length > 110000:
            content = self.token_slice(content)
        message_text = [
            {"role": "system", "content": "You are a cybersecurity expert specializing in analyzing malicious packages in package managers. Your task is to extract specific entity information from the given text, focusing only on the entities defined in the entity description."},
            {"role": "user", "content": "[**content**]:\n" + content + "\n\n[**potential malicious package name**]:\n" + str(potential_entity) + "\n\n[**entity description**]:\n" + self.entity + "\n\n" + self.entityextract_prompt + "\n\n"}
        ]
        extracted_entity = self.azure_query(message_text)
        return extracted_entity

    def entity_realtion_llm(self, content, extracted_entity):
        # 统计 token 的数量
        token_length = self.num_tokens_from_messages(content)
        max_tokens = 110000 - int(1.0 * token_length)
        if token_length > 110000:
            content = self.token_slice(content)
        message_text = [
            {"role": "system", "content": "You are a cybersecurity expert specializing in analyzing relationships between entities in malicious package reports. Your task is to analyze the relationships between the extracted entities by referring to the original content, and organize them into package-centric JSON objects."},
            {"role": "user", "content": "[**content**]:\n" + content + "\n\n[**extracted entities**]:\n" + extracted_entity + "\n\n" + self.entityrelation_prompt + "\n\n"}
        ]
        entity_realtion = self.azure_query(message_text)
        return entity_realtion

    def info_verify_llm(self, content, entity_realtion):
        # 统计 token 的数量
        token_length = self.num_tokens_from_messages(content)
        max_tokens = 110000 - int(1.0 * token_length)
        if token_length > 110000:
            content = self.token_slice(content)
        message_text = [
            {"role": "system", "content": "You are a cybersecurity expert specializing in verifying the accuracy of extracted information about malicious packages in package managers. Your task is to cross-check the extracted entities and their relationships against the original content, ensuring all information is accurate and supported by the text."},
            {"role": "user", "content": "[**content**]:\n" + content + "\n\n[**entities and relation**]:\n" + entity_realtion + "\n\n" + self.infoverify_prompt + "\n\n"}
        ]
        entity_validated = self.azure_query(message_text)
        return entity_validated

    def process_content(self, intell_source_dir, file_path, file_name):
        self.intell_source_dir = intell_source_dir
        json_file_name = os.path.join(self.json_dir, self.intell_source_dir, file_name.replace(".txt", ""))
        content = self.read_txt(file_path)
        self.load_dealt_pkgs()
        self.load_common_words()
        re_pkgnames = self.extract_package_names(content)
        # 删除停用词
        filtered_words = [word for word in re_pkgnames if word not in stop_words]
        llm_entities = self.entity_extract_llm(content, filtered_words)
        self.save_json(llm_entities, json_file_name + "_extract_gpt4.json")
        llm_relations = self.entity_realtion_llm(content, llm_entities)
        self.save_json(llm_relations, json_file_name + "_relation_gpt4.json")
        llm_verify = self.info_verify_llm(content, llm_relations)
        self.save_json(llm_verify, json_file_name + "_verify_gpt4.json")


if __name__ == '__main__':
    ltmgpt = LTMGPT()
    ltmgpt.process_content("jfrog", "/Users/blue/Documents/GitHub/IntelliRadar/Dataset/Content/jfrog/20240406_151844_572156.txt", "20240406_151844_572156.txt")