# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : reddit_collect.py
# @Project  : SCC_Intelligence
# Time      : 19/4/24 5:06 pm
# version   : python 3.8
# Description：
"""

import csv
import praw
from datetime import datetime


class RedditCollect:
    def __init__(self):
        self.client_id = 'iV-ef53EmAfBoz5AkekvQw'
        self.client_secret = 'IpiY_5kH56aH9ZNcnZSr889n0czZ3w'
        self.username = 'iBlueair'
        self.password = 'guowenbo1011'
        # Initialize praw instance
        self.reddit = praw.Reddit(
            client_id=self.client_id,  # Replace with your client ID
            client_secret=self.client_secret,  # Replace with your client secret
            user_agent='SCC'  # Replace with your user agent string
        )
        self.post_link_list = []

    def post_links(self):
        with open('pagelinks/malicious-Reddit-Search.csv', 'r') as f:
            csvreader = csv.reader(f)
            next(csvreader)
            for row in csvreader:
                url = row[1]
                self.post_link_list.append(url)

    def post_collect(self):
        self.post_links()
        for url in self.post_link_list:
            print(url)
            submission = self.reddit.submission(url=url)
            print(submission)
            print('Title:', submission.title)
            print('Text:', submission.selftext)
            created_time = datetime.utcfromtimestamp(submission.created_utc)
            print('Created at:', created_time.strftime('%Y-%m-%d %H:%M:%S UTC'))  # Format date time    
            submission.comments.replace_more(limit=50)
            for comment in submission.comments.list():
                print('Comment:', comment.body)


    def post_search(self):

        subreddit = self.reddit.subreddit('Python')

        query = 'malicious'

        search_results = subreddit.search(query, sort='Relevance', limit=100)  
        for post in search_results:
            post_url = post.url
            post_title = post.title
            created_time = datetime.utcfromtimestamp(post.created_utc) 
            print(post_title) 
            print(post_url)
            print(created_time) 




if __name__ == '__main__':
    reddit = RedditCollect()
    reddit.post_collect()
    # reddit.post_search()