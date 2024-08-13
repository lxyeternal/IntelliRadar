# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : abstractgens.py
# @Project  : PMonitor
# Time      : 4/2/24 4:15 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""


import torch
from transformers import PegasusForConditionalGeneration, PegasusTokenizer



def generate_abstract(src_text):
    model_name='google/pegasus-large'
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    tokenizer = PegasusTokenizer.from_pretrained(model_name)
    model = PegasusForConditionalGeneration.from_pretrained(model_name).to(device)

    batch = tokenizer(src_text, truncation=True, padding='longest', return_tensors="pt").to(device)
    translated = model.generate(**batch)
    tgt_text = tokenizer.batch_decode(translated, skip_special_tokens=True)
    return tgt_text

src_text = ["""China’s Huawei overtook Samsung Electronics as the world’s biggest seller of mobile phones in the second quarter of 2020, shipping 55.8 million devices compared to Samsung’s 53.7 million, according to data from research firm Canalys. While Huawei’s sales fell 5 per cent from the same quarter a year earlier, South Korea’s Samsung posted a bigger drop of 30 per cent, owing to disruption from the coronavirus in key markets such as Brazil, the United States and Europe, Canalys said. Huawei’s overseas shipments fell 27 per cent in Q2 from a year earlier, but the company increased its dominance of the China market which has been faster to recover from COVID-19 and where it now sells over 70 per cent of its phones. “Our business has demonstrated exceptional resilience in these difficult times,” a Huawei spokesman said. “Amidst a period of unprecedented global economic slowdown and challenges, we’re continued to grow and further our leadership position.” Nevertheless, Huawei’s position as number one seller may prove short-lived once other markets recover given it is mainly due to economic disruption, a senior Huawei employee with knowledge of the matter told Reuters. Apple is due to release its Q2 iPhone shipment data on Friday.""" ]


print(generate_abstract(src_text))