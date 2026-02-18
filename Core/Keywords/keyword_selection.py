#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import numpy as np
from gensim import corpora
from Core.Keywords.text_cleaning import preprocess_text
from collections import defaultdict
from gensim.models.ldamodel import LdaModel
from sklearn.decomposition import NMF
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer


class TextAnalyzer:

    def __init__(self, directory):
        self.directory = directory
        self.documents_dict = {}
        self.documents = []

    def load_documents(self):
        docu_files = os.listdir(self.directory)
        for file in docu_files:
            with open(os.path.join(self.directory, file), "r", encoding="utf-8") as f:
                text = f.read()
                self.documents_dict[file] = preprocess_text(text)
                self.documents.append(preprocess_text(text))

    def extract_keywords(self, top_n=25):
        """Extract top N keywords across all documents using TF-IDF."""
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(self.documents)
        feature_array = vectorizer.get_feature_names_out()
        tfidf_scores = defaultdict(float)
        for doc in range(tfidf_matrix.shape[0]):
            for word_idx in tfidf_matrix[doc, :].nonzero()[1]:
                tfidf_scores[feature_array[word_idx]] += tfidf_matrix[doc, word_idx]
        top_keywords = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        for word, score in top_keywords:
            print(f"{word}: {score:.4f}")
        return [word for word, score in top_keywords]

    def lda_topics(self):
        """Extract topics using LDA."""
        tokenized_documents = [word_tokenize(doc.lower()) for doc in self.documents]
        dictionary = corpora.Dictionary(tokenized_documents)
        corpus = [dictionary.doc2bow(text) for text in tokenized_documents]
        lda_model = LdaModel(corpus, num_topics=5, id2word=dictionary, passes=50)
        for topic_index in range(lda_model.num_topics):
            words = lda_model.show_topic(topic_index, topn=25)
            topic_keywords = [word for word, prob in words]
            print(f"Topic {topic_index + 1} keywords: {topic_keywords}")

    def extract_unique_keywords(self, top_n=10):
        document_texts = list(self.documents_dict.values())

        def tokenize(text):
            return text.split()

        vectorizer = TfidfVectorizer(tokenizer=tokenize)
        tfidf_matrix = vectorizer.fit_transform(document_texts)
        feature_array = vectorizer.get_feature_names_out()
        for doc_name, _ in self.documents_dict.items():
            doc_idx = list(self.documents_dict.keys()).index(doc_name)
            doc_tfidf = tfidf_matrix[doc_idx, :].toarray().flatten()
            sorted_indices = np.argsort(doc_tfidf)[::-1]
            doc_unique_keywords = [feature_array[idx] for idx in sorted_indices if doc_tfidf[idx] > 0][:top_n]
            print(f"{doc_name} unique keywords: {doc_unique_keywords}")

    def extract_extremely_unique_keywords(self, top_n=25):
        """Extract keywords that appear in the fewest documents."""
        doc_freq = defaultdict(int)
        tokenized_docs = {doc: content.lower().split() for doc, content in self.documents_dict.items()}
        for tokens in tokenized_docs.values():
            for token in set(tokens):
                doc_freq[token] += 1
        for doc, tokens in tokenized_docs.items():
            least_common_tokens = sorted(tokens, key=lambda token: doc_freq[token])[:top_n]
            print(f"{doc} unique keywords: {least_common_tokens}")

    def nmf_topics(self, n_topics=5, n_words=25):
        vectorizer = TfidfVectorizer(stop_words='english')
        doc_word_matrix = vectorizer.fit_transform(self.documents)
        nmf_model = NMF(n_components=n_topics)
        nmf_model.fit(doc_word_matrix)
        words = vectorizer.get_feature_names_out()
        topics = {}
        for i, topic in enumerate(nmf_model.components_):
            topics[f"Topic {i}"] = [words[i] for i in topic.argsort()[-n_words:]]
            print(f"Topic {i + 1}: {', '.join(topics[f'Topic {i}'])}")
        return topics


if __name__ == '__main__':
    analyzer = TextAnalyzer("maltext")
    analyzer.load_documents()
    analyzer.extract_keywords()
    analyzer.lda_topics()
    analyzer.nmf_topics()
    analyzer.extract_extremely_unique_keywords()
    analyzer.extract_unique_keywords()
