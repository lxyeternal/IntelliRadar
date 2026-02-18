#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import torch
import argparse
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import json
from tqdm import tqdm

class SecBERTNER:
    def __init__(self, model_name="jackaduma/SecBERT", device=None):
        """
        初始化SecBERT实体识别模型
        
        Args:
            model_name: 模型名称或路径
            device: 设备 (None为自动选择, 'cpu'或'cuda')
        """
        self.model_name = model_name
        
        # 自动选择设备
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"使用设备: {self.device}")
        print(f"加载模型: {model_name}")
        
        # 加载分词器和模型
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name).to(self.device)
        
        # 创建NER管道
        self.ner_pipeline = pipeline(
            "ner",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1,
            aggregation_strategy="simple"  # 合并相同实体的子词
        )
        
        print("模型加载完成")
    
    def process_text(self, text):
        """
        处理单个文本，识别实体
        
        Args:
            text: 输入文本
            
        Returns:
            识别出的实体列表
        """
        # 处理文本
        entities = self.ner_pipeline(text)
        
        # 格式化结果
        formatted_entities = []
        for entity in entities:
            formatted_entities.append({
                "entity": entity["word"],
                "type": entity["entity_group"],
                "score": float(entity["score"]),
                "start": entity["start"],
                "end": entity["end"]
            })
            
        return formatted_entities
    
    def process_file(self, input_file, output_file=None):
        """
        处理文本文件，识别实体
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径 (如果为None，则使用默认命名)
            
        Returns:
            输出文件路径
        """
        # 如果没有指定输出文件，则使用默认命名
        if output_file is None:
            base_name = os.path.basename(input_file)
            name_without_ext = os.path.splitext(base_name)[0]
            output_file = os.path.join(os.path.dirname(input_file), f"{name_without_ext}_entities.json")
        
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 处理文本
        entities = self.process_text(text)
        
        # 保存结果
        result = {
            "text": text,
            "entities": entities
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"实体识别结果已保存到: {output_file}")
        return output_file
    
    def process_directory(self, input_dir, output_dir=None, file_extension=".txt"):
        """
        处理目录中的所有文本文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录 (如果为None，则使用输入目录)
            file_extension: 要处理的文件扩展名
            
        Returns:
            处理的文件数量
        """
        # 如果没有指定输出目录，则使用输入目录
        if output_dir is None:
            output_dir = input_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取所有文件
        files = [f for f in os.listdir(input_dir) if f.endswith(file_extension)]
        
        # 处理每个文件
        for file in tqdm(files, desc="处理文件"):
            input_file = os.path.join(input_dir, file)
            name_without_ext = os.path.splitext(file)[0]
            output_file = os.path.join(output_dir, f"{name_without_ext}_entities.json")
            
            try:
                self.process_file(input_file, output_file)
            except Exception as e:
                print(f"处理文件 {file} 时出错: {e}")
        
        return len(files)

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='使用SecBERT进行实体识别')
    parser.add_argument('--input', required=True, help='输入文件或目录路径')
    parser.add_argument('--output', help='输出文件或目录路径')
    parser.add_argument('--model', default='jackaduma/SecBERT', help='模型名称或路径')
    parser.add_argument('--device', choices=['cpu', 'cuda'], help='使用的设备 (cpu或cuda)')
    parser.add_argument('--ext', default='.txt', help='要处理的文件扩展名 (仅在处理目录时有效)')
    
    args = parser.parse_args()
    
    # 初始化模型
    ner = SecBERTNER(model_name=args.model, device=args.device)
    
    # 处理输入
    if os.path.isdir(args.input):
        # 处理目录
        processed = ner.process_directory(args.input, args.output, args.ext)
        print(f"成功处理了 {processed} 个文件")
    else:
        # 处理单个文件
        ner.process_file(args.input, args.output)

if __name__ == "__main__":
    main() 