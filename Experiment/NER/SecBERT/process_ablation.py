#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import json
from tqdm import tqdm

from secbert_ner import SecBERTNER

INPUT_FOLDER = "/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq2/manual/ablation"
OUTPUT_FOLDER = "SecBERT_entity"

MAX_TOKENS = 300


def process_long_text(ner, text, tokenizer):
    """
    Process long text by splitting it into smaller chunks.

    Args:
        ner: SecBERTNER instance
        text: Input text
        tokenizer: Tokenizer instance

    Returns:
        Merged list of entities
    """
    sentences = text.replace('\n', ' ').split('. ')
    if sentences[-1] == '':
        sentences = sentences[:-1]

    all_entities = []
    current_chunk = ""
    current_tokens = []
    offset = 0

    for sentence in sentences:
        if sentence:
            sentence_with_period = sentence + '. '
        else:
            continue

        sentence_tokens = tokenizer.tokenize(sentence_with_period)

        if len(current_tokens) + len(sentence_tokens) > MAX_TOKENS:
            if current_chunk:
                try:
                    chunk_entities = ner.process_text(current_chunk)

                    for entity in chunk_entities:
                        entity['start'] += offset
                        entity['end'] += offset

                    all_entities.extend(chunk_entities)
                except Exception as e:
                    print(f"Error processing text chunk: {e}")

                offset += len(current_chunk)
                current_chunk = sentence_with_period
                current_tokens = sentence_tokens
            else:
                # Single sentence exceeds max tokens, force split by words
                print(f"Warning: found long sentence with {len(sentence_tokens)} tokens, attempting further split")

                words = sentence_with_period.split()
                sub_chunk = ""
                sub_tokens = []

                for word in words:
                    word_tokens = tokenizer.tokenize(word + " ")

                    if len(sub_tokens) + len(word_tokens) > MAX_TOKENS:
                        if sub_chunk:
                            try:
                                sub_entities = ner.process_text(sub_chunk)

                                for entity in sub_entities:
                                    entity['start'] += offset
                                    entity['end'] += offset

                                all_entities.extend(sub_entities)
                            except Exception as e:
                                print(f"Error processing sub-chunk: {e}")

                            offset += len(sub_chunk)

                            sub_chunk = word + " "
                            sub_tokens = word_tokens
                        else:
                            print(f"Warning: skipping overly long word: {word}")
                            offset += len(word) + 1
                    else:
                        sub_chunk += word + " "
                        sub_tokens.extend(word_tokens)

                if sub_chunk:
                    try:
                        sub_entities = ner.process_text(sub_chunk)

                        for entity in sub_entities:
                            entity['start'] += offset
                            entity['end'] += offset

                        all_entities.extend(sub_entities)
                    except Exception as e:
                        print(f"Error processing final sub-chunk: {e}")

                    offset += len(sub_chunk)

                current_chunk = ""
                current_tokens = []
        else:
            current_chunk += sentence_with_period
            current_tokens.extend(sentence_tokens)

    if current_chunk:
        try:
            chunk_entities = ner.process_text(current_chunk)

            for entity in chunk_entities:
                entity['start'] += offset
                entity['end'] += offset

            all_entities.extend(chunk_entities)
        except Exception as e:
            print(f"Error processing final text chunk: {e}")

    return all_entities


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print("Initializing SecBERT model...")
    model_name = "jackaduma/SecBERT"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    ner = SecBERTNER(model_name=model_name)

    print(f"Processing folder: {INPUT_FOLDER}")
    print(f"Results will be saved to: {OUTPUT_FOLDER}")

    txt_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.txt')]
    print(f"Found {len(txt_files)} txt files:")
    for txt_file in txt_files:
        print(f"  - {txt_file}")

    success_count = 0
    error_count = 0

    for txt_file in tqdm(txt_files, desc="Processing files"):
        input_path = os.path.join(INPUT_FOLDER, txt_file)
        name_without_ext = os.path.splitext(txt_file)[0]
        output_path = os.path.join(OUTPUT_FOLDER, f"{name_without_ext}.json")

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()

            entities = process_long_text(ner, text, tokenizer)

            result = {
                "text": text,
                "entities": entities
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            success_count += 1

        except Exception as e:
            print(f"Error processing file {txt_file}: {e}")
            error_count += 1

    print(f"Processing complete. Success: {success_count}, Failed: {error_count}")
    print(f"Results saved in {OUTPUT_FOLDER} folder")


if __name__ == "__main__":
    main()
