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
        Initialize SecBERT NER model.

        Args:
            model_name: Model name or path
            device: Device (None for auto-select, 'cpu' or 'cuda')
        """
        self.model_name = model_name

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Using device: {self.device}")
        print(f"Loading model: {model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name).to(self.device)

        self.ner_pipeline = pipeline(
            "ner",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1,
            aggregation_strategy="simple"
        )

        print("Model loaded successfully")

    def process_text(self, text):
        """
        Process a single text and recognize entities.

        Args:
            text: Input text

        Returns:
            List of recognized entities
        """
        entities = self.ner_pipeline(text)

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
        Process a text file and recognize entities.

        Args:
            input_file: Input file path
            output_file: Output file path (uses default naming if None)

        Returns:
            Output file path
        """
        if output_file is None:
            base_name = os.path.basename(input_file)
            name_without_ext = os.path.splitext(base_name)[0]
            output_file = os.path.join(os.path.dirname(input_file), f"{name_without_ext}_entities.json")

        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()

        entities = self.process_text(text)

        result = {
            "text": text,
            "entities": entities
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"Entity recognition results saved to: {output_file}")
        return output_file

    def process_directory(self, input_dir, output_dir=None, file_extension=".txt"):
        """
        Process all text files in a directory.

        Args:
            input_dir: Input directory
            output_dir: Output directory (uses input directory if None)
            file_extension: File extension to process

        Returns:
            Number of processed files
        """
        if output_dir is None:
            output_dir = input_dir

        os.makedirs(output_dir, exist_ok=True)

        files = [f for f in os.listdir(input_dir) if f.endswith(file_extension)]

        for file in tqdm(files, desc="Processing files"):
            input_file = os.path.join(input_dir, file)
            name_without_ext = os.path.splitext(file)[0]
            output_file = os.path.join(output_dir, f"{name_without_ext}_entities.json")

            try:
                self.process_file(input_file, output_file)
            except Exception as e:
                print(f"Error processing file {file}: {e}")

        return len(files)


def main():
    parser = argparse.ArgumentParser(description='Named entity recognition using SecBERT')
    parser.add_argument('--input', required=True, help='Input file or directory path')
    parser.add_argument('--output', help='Output file or directory path')
    parser.add_argument('--model', default='jackaduma/SecBERT', help='Model name or path')
    parser.add_argument('--device', choices=['cpu', 'cuda'], help='Device to use (cpu or cuda)')
    parser.add_argument('--ext', default='.txt', help='File extension to process (only effective for directories)')

    args = parser.parse_args()

    ner = SecBERTNER(model_name=args.model, device=args.device)

    if os.path.isdir(args.input):
        processed = ner.process_directory(args.input, args.output, args.ext)
        print(f"Successfully processed {processed} files")
    else:
        ner.process_file(args.input, args.output)


if __name__ == "__main__":
    main()
