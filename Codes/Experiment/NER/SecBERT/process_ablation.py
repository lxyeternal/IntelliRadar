#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import json
from tqdm import tqdm

# 导入SecBERTNER类
from secbert_ner import SecBERTNER

# 指定输入和输出路径
INPUT_FOLDER = "/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq2/manual/ablation"
OUTPUT_FOLDER = "SecBERT_entity"

# 设置最大token长度
MAX_TOKENS = 300  # 模型最大长度为512，留出一些余量

def process_long_text(ner, text, tokenizer):
    """
    处理长文本，将其分割成较小的块进行处理
    
    Args:
        ner: SecBERTNER实例
        text: 输入文本
        tokenizer: 分词器
        
    Returns:
        合并后的实体列表
    """
    # 按句子分割文本
    sentences = text.replace('\n', ' ').split('. ')
    if sentences[-1] == '':
        sentences = sentences[:-1]
    
    # 初始化结果列表
    all_entities = []
    current_chunk = ""
    current_tokens = []
    offset = 0
    
    # 逐句处理
    for sentence in sentences:
        # 如果句子不为空，加上句号
        if sentence:
            sentence_with_period = sentence + '. '
        else:
            continue
            
        # 计算句子的token数
        sentence_tokens = tokenizer.tokenize(sentence_with_period)
        
        # 如果当前块加上这个句子会超出最大token数，先处理当前块
        if len(current_tokens) + len(sentence_tokens) > MAX_TOKENS:
            if current_chunk:
                try:
                    # 处理当前块
                    chunk_entities = ner.process_text(current_chunk)
                    
                    # 调整实体位置
                    for entity in chunk_entities:
                        entity['start'] += offset
                        entity['end'] += offset
                        
                    # 添加到结果列表
                    all_entities.extend(chunk_entities)
                except Exception as e:
                    print(f"处理文本块时出错: {e}")
                
                # 重置当前块，更新偏移量
                offset += len(current_chunk)
                current_chunk = sentence_with_period
                current_tokens = sentence_tokens
            else:
                # 如果单个句子就超长，则强制分割
                print(f"警告：发现超长句子，token数为 {len(sentence_tokens)}，尝试进一步分割")
                
                # 将句子分成更小的片段
                words = sentence_with_period.split()
                sub_chunk = ""
                sub_tokens = []
                
                for word in words:
                    word_tokens = tokenizer.tokenize(word + " ")
                    
                    if len(sub_tokens) + len(word_tokens) > MAX_TOKENS:
                        if sub_chunk:
                            try:
                                # 处理子块
                                sub_entities = ner.process_text(sub_chunk)
                                
                                # 调整实体位置
                                for entity in sub_entities:
                                    entity['start'] += offset
                                    entity['end'] += offset
                                    
                                # 添加到结果列表
                                all_entities.extend(sub_entities)
                            except Exception as e:
                                print(f"处理子文本块时出错: {e}")
                            
                            # 更新偏移量
                            offset += len(sub_chunk)
                            
                            # 重置子块
                            sub_chunk = word + " "
                            sub_tokens = word_tokens
                        else:
                            # 单词太长，跳过
                            print(f"警告：跳过超长单词: {word}")
                            offset += len(word) + 1
                    else:
                        sub_chunk += word + " "
                        sub_tokens.extend(word_tokens)
                
                # 处理最后一个子块
                if sub_chunk:
                    try:
                        sub_entities = ner.process_text(sub_chunk)
                        
                        # 调整实体位置
                        for entity in sub_entities:
                            entity['start'] += offset
                            entity['end'] += offset
                            
                        # 添加到结果列表
                        all_entities.extend(sub_entities)
                    except Exception as e:
                        print(f"处理最后一个子文本块时出错: {e}")
                    
                    # 更新偏移量
                    offset += len(sub_chunk)
                
                # 重置当前块
                current_chunk = ""
                current_tokens = []
        else:
            # 如果不超长，添加到当前块
            current_chunk += sentence_with_period
            current_tokens.extend(sentence_tokens)
    
    # 处理最后一个块
    if current_chunk:
        try:
            chunk_entities = ner.process_text(current_chunk)
            
            # 调整实体位置
            for entity in chunk_entities:
                entity['start'] += offset
                entity['end'] += offset
                
            # 添加到结果列表
            all_entities.extend(chunk_entities)
        except Exception as e:
            print(f"处理最后一个文本块时出错: {e}")
    
    return all_entities

def main():
    # 确保输出目录存在
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # 初始化模型和tokenizer
    print("初始化SecBERT模型...")
    model_name = "jackaduma/SecBERT"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    ner = SecBERTNER(model_name=model_name)
    
    # 处理目录
    print(f"处理文件夹: {INPUT_FOLDER}")
    print(f"结果将保存到: {OUTPUT_FOLDER}")
    
    # 获取所有txt文件
    txt_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.txt')]
    print(f"找到 {len(txt_files)} 个txt文件:")
    for txt_file in txt_files:
        print(f"  - {txt_file}")
    
    # 处理每个文件
    success_count = 0
    error_count = 0
    
    for txt_file in tqdm(txt_files, desc="处理文件"):
        input_path = os.path.join(INPUT_FOLDER, txt_file)
        name_without_ext = os.path.splitext(txt_file)[0]
        output_path = os.path.join(OUTPUT_FOLDER, f"{name_without_ext}.json")
        
        try:
            # 读取文本
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # 处理长文本
            entities = process_long_text(ner, text, tokenizer)
            
            # 保存结果
            result = {
                "text": text,
                "entities": entities
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            success_count += 1
            
        except Exception as e:
            print(f"处理文件 {txt_file} 时出错: {e}")
            error_count += 1
    
    print(f"处理完成，成功: {success_count}，失败: {error_count}")
    print(f"结果保存在 {OUTPUT_FOLDER} 文件夹中")

if __name__ == "__main__":
    main() 