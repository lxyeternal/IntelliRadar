# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : sankey.js
# @Project  : PMonitor
# Time      : 31/1/24 4:21 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""

import re
import os
import nltk
import gensim
import numpy as np
from numpy import dot
from gensim import corpora
from numpy.linalg import norm
from collections import Counter
from nltk.corpus import stopwords
from sklearn.svm import OneClassSVM
from nltk.tokenize import word_tokenize
from sklearn.decomposition import PCA
from transformers import BertTokenizer, BertModel
from Codes.Keywords.textclean import preprocess_text
from gensim.models.doc2vec import Doc2Vec, TaggedDocument


nltk.download('punkt')
nltk.download('stopwords')


class OneSVMMatch:
    def __init__(self):
        self.folder_path = '../Keywords/maltext/'
        self.pca = PCA(n_components=50)
        self.tagged_data = []

    def preprocess(self, text):
        text = preprocess_text(text)
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalpha()]
        words = [word for word in words if word not in stopwords.words('english')]
        return words

    def load_dataset(self):
        for idx, filename in enumerate(os.listdir(self.folder_path)):
            if filename.endswith('.txt'):
                path = os.path.join(self.folder_path, filename)
                with open(path, 'r', encoding='utf-8') as file:
                    text = file.read()
                    self.tagged_data.append(TaggedDocument(words=self.preprocess(text), tags=[str(idx)]))


    def train_doc2vec(self):
        model = Doc2Vec(vector_size=100, window=2, min_count=1, workers=4, epochs=40)
        model.build_vocab(self.tagged_data)
        model.train(self.tagged_data, total_examples=model.corpus_count, epochs=model.epochs)
        return model


    def train_oneclasssvm(self, model):
        vectors = [model.infer_vector(doc.words) for doc in self.tagged_data]
        reduced_vectors = self.pca.fit_transform(vectors)
        svm_model = OneClassSVM(gamma='auto').fit(reduced_vectors)
        return svm_model


    def predict(self, model, svm_model, new_text):
        processed_new_text = self.preprocess(new_text)
        new_text_vector = model.infer_vector(processed_new_text)
        reduced_new_text_vector = self.pca.transform([new_text_vector])
        prediction = svm_model.predict(reduced_new_text_vector)
        return prediction

    def main(self):
        self.load_dataset()
        doc2vec_model = self.train_doc2vec()
        svm_model = self.train_oneclasssvm(doc2vec_model)
        new_text = "A group with the ominous name “EsqueleSquad”, which translates to “Skeletons Squad” in Catalan, published over 5000 malicious packages up until last weekend. This group is linked to several other packages uploaded in early January, all dropping malicious executables using different methods."
        prediction = self.predict(doc2vec_model, svm_model, new_text)
        print(prediction)



class BertMatch:
    def __init__(self):
        self.folder_path = '../Keywords/maltext/'
        self.pca = PCA(n_components=50)
        self.tagged_data = []


    def bert_embedding(self, model, tokenizer, text):
        inputs = tokenizer(text, return_tensors="pt")
        outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).squeeze().detach().numpy()


    def similarity(self, embedding1, embedding2):
        cosine_similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        return cosine_similarity


    def main(self):
    # 加载预训练的BERT模型和分词器
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertModel.from_pretrained('bert-base-uncased')
        text1 = """"""
        text2 = """"""
        embedding1 = self.bert_embedding(model, tokenizer, text1)
        embedding2 = self.bert_embedding(model, tokenizer, text2)
        cosine_similarity = self.similarity(embedding1, embedding2)
        print("语义相似度:", cosine_similarity)


class TopicMatch:
    def __init__(self, num_topics=5):
        self.dictionary = None
        self.model = None
        self.num_topics = num_topics
        self.corpus = None
        self.topic_distributions = []
        self.remove_chars = ['``', "''", ',', '.', ';', ':', '?', '!', "'", '"', '(', ')', '[', ']', '{', '}', '&', '...', "-"]


    def read_documents(self, folder_path):
        documents = []
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
                    documents.append(file.read())
        return documents

    def load_stop_words(self):
        stop_words = list()
        with open("../../archive/en_stopwords.txt", 'r', encoding='utf-8') as file:
            for line in file:
                stop_words.append(line.strip())
        return stop_words

    def cosine_similarity(self, vec1, vec2):
        # 计算余弦相似度
        return dot(vec1, vec2) / (norm(vec1) * norm(vec2))

    def preprocess(self, documents):
        # 分词和去除停用词
        stop_words = set(stopwords.words('english'))
        stop_words.update(self.load_stop_words())
        texts = [
            [word for word in word_tokenize(document.lower())
             if word not in stop_words and word not in self.remove_chars]
            for document in documents
        ]
        return texts

    def get_document_topics(self, text):
        # 预处理单个文档
        preprocessed_text = self.preprocess([text])[0]
        # 转换为词袋表示
        bow = self.dictionary.doc2bow(preprocessed_text)
        # 获取文档的主题分布
        document_topics = self.model.get_document_topics(bow)
        return document_topics

    def train(self, folder_path):
        # 从指定文件夹读取文档
        documents = self.read_documents(folder_path)
        # 预处理文档
        texts = self.preprocess(documents)
        # 创建字典
        self.dictionary = corpora.Dictionary(texts)
        # 创建语料库
        self.corpus = [self.dictionary.doc2bow(text) for text in texts]
        # 训练LDA模型
        self.model = gensim.models.ldamodel.LdaModel(self.corpus, num_topics=self.num_topics, id2word=self.dictionary, passes=15)
        # 保存每个文档的主题分布
        self.topic_distributions = [self.model.get_document_topics(bow) for bow in self.corpus]

    def average_topic_distribution(self):
        # 计算平均主题分布
        avg_distribution = [0] * self.num_topics
        for dist in self.topic_distributions:
            for topic, prob in dist:
                avg_distribution[topic] += prob / len(self.topic_distributions)
        return avg_distribution


    def get_similarity_with_corpus(self, new_document):
        # 获取新文档的主题分布
        new_doc_topics = self.get_document_topics(new_document)
        new_doc_distribution = [0] * self.num_topics
        for topic, prob in new_doc_topics:
            new_doc_distribution[topic] = prob
        # 获取平均主题分布
        avg_distribution = self.average_topic_distribution()
        # 计算相似度
        similarity = self.cosine_similarity(new_doc_distribution, avg_distribution)
        return similarity

    def main(self):
        self.train('../Keywords/maltext/')
        new_document = """"""
        similarity = self.get_similarity_with_corpus(new_document)
        print("新文档与训练文档集的主题相似度:", similarity)



class KeywordsMatch:
    def __init__(self):
        # 定义关键词和权重
        self.weights = {
            "malicious": 5,
            "malicious_behavior": 3,
            "package_manager": 2,
            "oss": 1
        }
        self.keyword_categories = {
            "malicious": set(["malicious", "security", "malware", "backdoor", "phishing", "cryptojacking", "typosquatting", "bitsquatting", "compromise", "ransomware", "trojan", "virus", "worm", "spyware", "adware", "botnet", "rootkit", "keylogger", "attack", "attacker", "injection", "hijacking", "spoofing", "phishing", "obfuscation"]),
            "malicious_behavior": set(["code execution", "information stealing", "remote control", "ransomware", "mining", "trojan", "backdoor", "zombie network", "encryption", "decryption", "encoding", "decoding", "injection", "overflow", "attack"]),
            "package_manager": set(["npm", "pypi", "python", "javascript", "js", "pypi.org", "npmjs.com", "nuget", "golang", "maven", "rubygems", "packagist", "cargo", "composer", "hackage", "cran", "conda", "swift", "cocoapods", "script", "code", "package.json", "requirements.txt", "package-lock.json", "pipfile", "pipfile.lock", "yarn.lock", "Gemfile", "Gemfile.lock", "Podfile", "Podfile.lock", "Cargo.toml", "Cargo.lock", "composer.json", "composer.lock", "Rakefile", "Gemspec"]),
            "oss": set(["registry", "package", "supply chain", "component", "dependency", "open source", "ecosystem", "conduct", "maintain", "maintainers", "maintainance", "management", "manager", "maintainers"])
        }

    def preprocess(self, text):
        # 简单的文本预处理
        return re.findall(r'\b\w+\b', text.lower())

    def match_keywords(self, text):
        words = self.preprocess(text)
        word_count = Counter(words)

        score = 0
        # 检查并计算得分
        for word in word_count:
            for category, keywords in self.keyword_categories.items():
                if word in keywords:
                    score += self.weights[category] * word_count[word]
                    break  # 避免一个单词被多次计分
        return score


if __name__ == '__main__':
    # tm = TopicMatch(num_topics=2)
    # tm.main()
    # bm = BertMatch()
    # bm.main()
    matcher = KeywordsMatch()
    text = """"""
    score = matcher.match_keywords(text)
    print("Score:", score)