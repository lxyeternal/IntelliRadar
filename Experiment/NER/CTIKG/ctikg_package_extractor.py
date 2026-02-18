import json
import os
import re
import openai
from openai import OpenAI
import time
import logging
from tqdm import tqdm
import nltk
import pandas as pd

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class CTIKGPackageExtractor:
    """Malicious package extractor based on CTIKG method"""

    def __init__(self, api_key="", model="gpt-4o", max_attempts=3):
        """Initialize extractor"""
        self.api_key = api_key
        self.model = model
        self.max_attempts = max_attempts

    def _openai_query(self, messages, max_tokens=16000, temperature=0.5, top_p=0.3,
                     frequency_penalty=0.0, presence_penalty=0.0,
                     response_format=None, seed=42):
        """
        Execute query using OpenAI API

        Args:
            messages: List of message objects for the conversation
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            frequency_penalty: Penalty for token frequency
            presence_penalty: Penalty for token presence
            response_format: Format of the response
            seed: Random seed for reproducibility

        Returns:
            str: Response content from OpenAI
        """
        client = OpenAI(api_key=self.api_key)

        wait_time = 10
        attempt = 0

        while attempt < self.max_attempts:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format=response_format,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    stop=None,
                    seed=seed,
                    stream=False
                )
                return response.choices[0].message.content
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1}: An error occurred: {e}")
                attempt += 1
                time.sleep(wait_time)
                wait_time += 5

        return ""

    def extract_packages_from_file(self, input_file, output_file):
        """Extract malicious package information from file and save to JSON"""
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()

        result = self.full_article_to_longmem(text)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"extracted_triples": result}, f, ensure_ascii=False, indent=2)

        return result

    def compute_full_extracted_triples(self, input_sentence):
        """Extract triples from input sentence"""
        def generate_prompt(text):
            promptmessage = [
            {
            "role": "user",
            "content":
            '''
            As an AI trained in entity extraction and relationship extraction, specializing in malicious package information. You are an advanced AI expert, and your output format MUST be a dictionary where the key is the source sentence and the value is a list consisting of extracted triples.

            A triple is a basic data structure used to represent knowledge graphs, which must have THREE elements: [Subject, Relation, Object]. For malicious packages, we are particularly interested in:
            1. PyPI and npm package names and their versions
            2. Relationships between packages and their malicious behaviors
            3. Relationships between packages and their developers/attackers

            Examples:
            [SUBJECT:axios-http, RELATION:version, OBJECT:0.1.0]
            [SUBJECT:discord-lofy, RELATION:steals, OBJECT:Discord tokens]
            [SUBJECT:color-rgba, RELATION:developed by, OBJECT:malicious actor]

            In entity extraction, follow these rules:
            Rule 1: Only extract triples related to malicious software packages, with special focus on PyPI and npm packages.
            Rule 2: Ensure your results are in Python dictionary format. An example is {source sentence1:[[subject1, relation1, object1],[subject2, relation2, object2]...]}
            Rule 3: You must use ellipsis in source sentences to save space. The output format should be "First word Second word ... penu word last word".
            '''
            },
            {"role": "assistant", "content": "I understand."},
            {"role": "user", "content": "Here is an example sentence: \"Researchers discovered a malicious npm package called discord-lofy, version 0.1.3, which steals users' Discord tokens and passwords.\""},
            {"role": "assistant", "content": "{Researchers discovered ... Discord tokens and passwords.:[[SUBJECT:discord-lofy,RELATION:is,OBJECT:malicious npm package],[SUBJECT:discord-lofy,RELATION:version,OBJECT:0.1.3],[SUBJECT:discord-lofy,RELATION:steals,OBJECT:Discord tokens],[SUBJECT:discord-lofy,RELATION:steals,OBJECT:passwords]]}"},
            {"role": "user", "content":
            """
            Here are my new sentences, extract all possible entity triples from them. Now, I start to give you sentences.\""""+text+
            """\"Now, my input text is over. You MUST follow the rules I told you before.
            """
            },
            ]
            return promptmessage

        def generate_prompt_basedon3(inSent, inlist):
            promptmessage = [
            {
            "role": "user",
            "content": 'You are responsible for combining three different entity extraction results from three different assistants extracting from the same sentence into one. A triple is a basic data structure used to represent knowledge graphs, which must have THREE elements: [Subject, Relation, Object]. The subject has the prefix "SUBJECT:", the relation has prefix "RELATION:", the object has prefix "OBJECT:". We are particularly interested in PyPI and npm package names and versions. The final result is a Python dictionary format. I want you to integrate these three results into one, discard exact duplicates, and discard triples that do not contain exactly 3 elements. The source sentence is '+str(inSent)+', the extracted triples results are'+str(inlist)+'Just answer me the final Python dictionary with triple format without any other words.'
            },
            ]
            return promptmessage

        def generate_prompt_postprocess(text):
            promptmessage = [
            {
            "role": "user",
            "content":
            '''
            You play the role of an entity extraction expert, specializing in malicious package information. Please modify/simplify/split the triples in my entity extraction results according to these rules:

            Rule 1: If a triple's subject or object contains pronouns, replace them with specific package names.
            Rule 2: Focus on PyPI and npm packages as subjects of triples, removing unnecessary suffixes.
            Rule 3: Split complex triples into multiple simpler forms. For example, [discord-lofy and axios-http, are, malicious packages] should be split into [discord-lofy, is, malicious package] and [axios-http, is, malicious package].
            Rule 4: Ensure version information is correctly extracted, in the format [package name, version, version number].
            Rule 5: Simplify subjects, objects, and relations to more concise expressions.
            Rule 6: Make sure the subject has prefix "SUBJECT:", relation has prefix "RELATION:", object has prefix "OBJECT:"
            '''
            +"Here is my entity extraction result:"+str(text)+"Now, apply the rules I told you. Write down your thought process, step by step. Finally, you MUST tell me the final new entity extraction result. Make sure your result contains a dictionary where the key is the original sentence and the value is a list consisting of extracted triples."
            },
            ]
            return promptmessage

        def get_only_triples(text):
            text = text.replace(': [', ':[')
            if "{" in text and "}" in text:
                start_index = text.rindex('{')
                end_index = text.rindex('}') + 1
                triple_only_text = text[start_index:end_index]
                if ":[" in triple_only_text and ']' in triple_only_text:
                    source_sentence = triple_only_text.split(':')[0]
                    source_sentence = source_sentence.split('{')[1]
                    words = source_sentence.split()
                    if len(words) <= 2:
                        abbreviation = source_sentence
                    else:
                        abbreviation = " ".join(words[:2]) + " ... " + " ".join(words[-2:])
                    triple_only_text = triple_only_text.replace(source_sentence, abbreviation)
            else:
                text = text.replace('\n', '')

                if ":[" in text and "]" in text:
                    start_index = text.rindex(':[')
                    end_index = text.rindex(']') + 1
                    triple_only_text = text[start_index:end_index]
                else:
                    if "[[" in text and "]]" in text:
                        start_index = text.rindex('[[')
                        end_index = text.rindex(']]') + 1
                        triple_only_text = text[start_index:end_index]
                    else:
                        triple_only_text = text
            return triple_only_text

        def clean_text(text):
            import string
            if not isinstance(text, str):
                return text
            cleaned_text = re.sub(r'[^\x20-\x7E]', '', text)
            cleaned_text = re.sub(r'[\s{}]+'.format(re.escape(string.punctuation)), '', cleaned_text)
            cleaned_text = re.sub(r'SUBJECT|RELATION|OBJECT', '', cleaned_text)
            return cleaned_text if cleaned_text else 'Null'

        single_sentence = input_sentence
        first_answer_list = []
        temperature_list = [1, 0.5, 0]

        for temp in temperature_list:
            content_first_extraction = self._openai_query(
                messages=generate_prompt(single_sentence),
                max_tokens=16000,
                temperature=temp,
            )
            cleaned_text = clean_text(str(content_first_extraction))

            if any(keyword in cleaned_text for keyword in ['CVE']):
                first_answer_list.append('ERROR')
            else:
                first_answer_list.append(get_only_triples(content_first_extraction))

        content_first_extraction_merged = self._openai_query(
            messages=generate_prompt_basedon3(single_sentence, first_answer_list[0:3]),
            max_tokens=16000,
            temperature=0.5,
        )
        content_first_extraction_merged = get_only_triples(content_first_extraction_merged)

        content_simple_version = self._openai_query(
            messages=generate_prompt_postprocess(content_first_extraction_merged),
            max_tokens=16000,
            temperature=0.7,
        )
        extracted_text = get_only_triples(content_simple_version)
        return extracted_text

    def clean_full_extracted_triples(self, text):
        """Clean and format extracted triples"""
        text = text.replace('\n', '')
        text = re.sub(r':\s+\[', r':[', text)
        text = re.sub(r'\s+\[', r'[', text)
        text = re.sub(r'\s+\]', r']', text)
        text = re.sub(r'\]\s*,\s*\]', ']]', text)

        triple_only_text = text
        if "[[" in text and "]]" in text:
            start_index = text.rindex('[[') + 1
            end_index = text.rindex(']]') + 1
            triple_only_text = text[start_index:end_index]
        else:
            if "[[" in text or "]]" in text:
                start_index = text.index('[')
                end_index = text.rindex(']') + 1
                triple_only_text = text[start_index:end_index]

        triple_only_text = triple_only_text.replace('"', '')
        triple_only_text = triple_only_text.replace("'", '')

        return triple_only_text

    def check_brackets(self, my_string):
        """Check if string starts and ends with brackets"""
        if my_string is None or len(my_string) == 0:
            return False
        my_string = my_string.strip()
        first_char_is_bracket = my_string[0] == '['
        last_char_is_bracket = my_string[-1] == ']'

        return first_char_is_bracket and last_char_is_bracket

    def checker(self, my_string):
        """Check if AI assistant's response is valid"""
        promptmessage = [{
            "role": "user",
            "content": 'You are a result checker. You are responsible for checking results from other AI assistants. The AI assistant might say "I am sorry, but I am Chat AI model and I am not able to do the task" or "You should do it by yourself" or "I am sorry, but I am not able to do the task". If you find those words or words with similar meaning, you must reply "ERROR", otherwise, you should reply "OK". Here is the result from another AI assistant: ' + str(my_string)}]

        result = self._openai_query(
            messages=promptmessage,
            max_tokens=1000,
            temperature=1,
        )
        return result

    def full_text_to_parts(self, text):
        """Split full text into manageable parts for large context models"""
        paragraphs = text.split('\n')
        paragraphs = [p.strip() for p in paragraphs if len(p.strip()) >= 20]

        max_chunk_size = 15000

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 1 > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n" + paragraph
                else:
                    current_chunk = paragraph

        if current_chunk:
            chunks.append(current_chunk)

        if not chunks:
            return [text] if text else []

        return chunks

    def merge_extracted_triples(self, longmem, shortmem, sentence):
        """Merge triples from long-term and short-term memory"""
        def generate_prompt(longmem, shortmem, sentence):
            promptmessage = [
            {
            "role": "user",
            "content":
            '''You are a triples integration assistant. Triple is a basic data structure, which describes concepts and their relationships. A triple in long-term and short-term memory MUST has THREE elements: [Subject, Relation, Object]. You are now reading a whole article and extract all triples from it. But you can only see part of the article at a time. To record all the triples from an article, you have the following long-term memory area to record the triples from the entire article parts you have already read.

            -The start of the long-term memory area-
            #Triples will be added here
            -The end of the long-term memory area-

            Second, you now see a part of this article. Based on this part, you already extract such triples and place them in your short-term memory:

            -The start of the short-term memory area-
            #Triples will be added here
            -The end of the short-term memory area-

            Third, now review your long-term memory and short-term memory. Modify the short-term memory into a new short-term memory. Follow these rules to modify triples in short-term memory to make them consistent with triples in long-term memory:

            Rule 1: You notice that in these triples, some triples have subjects and objects that contain partially identical terms and refer to the same specific nouns, but these specific nouns have prefixes/suffixes/modifiers that make them not identical. You should delete the prefixes/suffixes/modifiers and unify them into the same specific nouns.

            Rule 2: Be especially careful that when you meet specific names of malicious packages, always use their specific names and remove the prefixes/suffixes/modifiers.

            Rule 3: Don't add non-existent triples to your new short-term memory.

            Rule 4: Don't add triples that don't exist in long-term memory or short-term memory to your new short-term memory.

            Rule 5: Don't add any example words in your new short-term memory area.

            Rule 6: New short-term memory area must start with \'-The start of new short-term memory area-\' and end with \'-The end of new short-term memory area-\'. A triple in new short-term memory MUST have THREE elements: [Subject, Relation, Object].
            '''
            },
            {"role": "assistant", 'content': 'Yes, I understand and will follow the rules completely.'},
            {"role": "user", 'content':
            '''
            -The start of the long-term memory area-
            ''' + str(longmem) + '''
            -The end of the long-term memory area-

            -The start of the short-term memory area-
            ''' + str(shortmem) + '''
            -The end of the short-term memory area-

            Now, follow the rules. Write down how you use the rule to modify the triples in short-term memory. Then, write down new short-term memory which must start with \'-The start of new short-term memory area-\' and end with \'-The end of new short-term memory area-\'
            '''
            },
            ]
            return promptmessage

        fullanswer = self._openai_query(
            messages=generate_prompt(longmem, shortmem, sentence),
            max_tokens=16000,
            temperature=0.7,
        )

        return fullanswer

    def full_article_to_longmem(self, single_article):
        """Process entire article and extract all triples"""
        grouped_texts_strings = self.full_text_to_parts(single_article)
        triple_cache = []
        text_cache = []
        longmem = ""

        for i in range(len(grouped_texts_strings)):
            this_time_test = grouped_texts_strings[i]

            print(f'Processing paragraph {i+1}/{len(grouped_texts_strings)}')
            print('Text content length:', len(this_time_test))

            triple = self.compute_full_extracted_triples(this_time_test)
            clean_triple_forMEM = self.clean_full_extracted_triples(triple)

            retry_count = 0
            while (any(keyword in clean_triple_forMEM for keyword in ['Formbook', 'XLoader', 'Leafminer', 'FinSpy', 'Kismet']) or
                   not self.check_brackets(clean_triple_forMEM) or
                   self.checker(triple) == 'ERROR') and retry_count < 3:
                print(f'Current short-term memory does not meet requirements, retrying {retry_count+1}')
                triple = self.compute_full_extracted_triples(this_time_test)
                clean_triple_forMEM = self.clean_full_extracted_triples(triple)
                retry_count += 1

            print('Current short-term memory:')
            print(clean_triple_forMEM)

            if i == 0:
                if self.check_brackets(clean_triple_forMEM):
                    longmem = clean_triple_forMEM
                else:
                    longmem = 'No longterm memory'
                triple_cache.append(clean_triple_forMEM)
                text_cache.append(this_time_test)
                print('First part processing completed')

            if i >= 1:
                print('Historical long-term memory:')
                print(longmem)
                original_longmem = longmem

                if len(longmem) >= 15000:
                    longmem = longmem[-8000:]
                    if '[' in longmem:
                        longmem = longmem[longmem.index('['):]

                if self.check_brackets(clean_triple_forMEM):
                    max_retries = 3
                    retry_count = 0
                    while retry_count < max_retries:
                        print(f'Attempting merge, try {retry_count+1}')
                        newlongmem = self.merge_extracted_triples(longmem, clean_triple_forMEM, this_time_test)
                        print('Thinking process:')
                        print(newlongmem)

                        newlongmem = newlongmem.replace('-The start of the new short-term memory area-', '-The start of new short-term memory area-')
                        newlongmem = newlongmem.replace('-The end of the new short-term memory area-', '-The end of new short-term memory area-')

                        if '-The start of new short-term memory area-' in newlongmem and '-The end of new short-term memory area-' in newlongmem and self.checker(newlongmem) != 'ERROR':
                            newlongmem = newlongmem[newlongmem.rindex('-The start of new short-term memory area-') + len('-The start of new short-term memory area-'):newlongmem.rindex('-The end of new short-term memory area-')]
                            if not any(keyword in newlongmem for keyword in ['Formbook', 'XLoader', 'Leafminer', 'FinSpy', 'Kismet']):
                                longmem = str(original_longmem) + ', ' + str(newlongmem)
                                break

                        retry_count += 1
                else:
                    longmem = original_longmem
                    print('Short-term memory is not a valid triple')

                print('After merging: The new long-term memory is:')
                print(longmem)

                try:
                    new_data = pd.DataFrame({
                        'single_article': [str(single_article)],
                        'longmem': [str(longmem)]
                    })

                    try:
                        longmem_cache = pd.read_excel('package_extraction_cache.xlsx')
                        longmem_cache = pd.concat([longmem_cache, new_data], ignore_index=True)
                    except FileNotFoundError:
                        longmem_cache = new_data

                    longmem_cache.to_excel('package_extraction_cache.xlsx', index=False)
                except Exception as e:
                    print(f"Error saving cache: {e}")

        return longmem


def process_all_files(input_dir, output_dir, api_key="", model="gpt-4o"):
    """Process all txt files in input directory and save results to output directory"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    extractor = CTIKGPackageExtractor(api_key=api_key, model=model)

    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    print(f"Found {len(txt_files)} txt files to process")

    for i, txt_file in enumerate(txt_files):
        input_path = os.path.join(input_dir, txt_file)
        output_path = os.path.join(output_dir, txt_file.replace('.txt', '.json'))

        print(f"Processing file {i+1}/{len(txt_files)}: {txt_file}")
        try:
            result = extractor.extract_packages_from_file(input_path, output_path)
            print(f"Successfully processed {txt_file}, saved to {output_path}")
        except Exception as e:
            print(f"Error processing {txt_file}: {e}")

    print(f"All files processed. Results saved to {output_dir}")


INPUT_DIR = "/Users/blue/Documents/Github/SCC_Intelligence/Codes/Experiment/rq2/manual/ablation"
OUTPUT_DIR = "./extracted_packages"
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = "gpt-4o"

if __name__ == "__main__":
    print(f"Processing files from: {INPUT_DIR}")
    print(f"Saving results to: {OUTPUT_DIR}")
    print(f"Using model: {MODEL}")
    process_all_files(INPUT_DIR, OUTPUT_DIR, API_KEY, MODEL)
