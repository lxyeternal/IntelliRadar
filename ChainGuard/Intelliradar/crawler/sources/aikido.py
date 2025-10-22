#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aikido Security API 数据采集器
"""

import requests
import json
import time
import os
from multiprocessing import Process, Value, Lock

def crawl_pages(process_id, start_page, step, shared_failures, lock):
    """主函数"""
    # 输出目录
    output_dir = "/Users/blue/Documents/Github/ChainGuard/Intelliradar/data/other"
    os.makedirs(output_dir, exist_ok=True)
    
    # 请求配置
    base_url = "https://app.aikido.dev/api/malware/packages"
    headers = {
        'cookie': 'locale=en; intercom-id-j0dzii6j=50027ef0-c161-4d62-8a4c-af4a548dbbf7; intercom-device-id-j0dzii6j=46920d67-cc1e-4360-91c9-09ef9d774e5e; _vwo_uuid_v2=DC4BD295D351580FB336F6ED13E4B58EE|30957938473ca706be82bfda4f546d8f; _vwo_uuid=DC4BD295D351580FB336F6ED13E4B58EE; _vwo_ds=3%241758180287%3A50.37439682%3A%3A; _vis_opt_s=1%7C; _vis_opt_test_cookie=1; __hstc=115122392.abff935bba6e41e01231c115ed358579.1758180289010.1758180289010.1758180289010.1; hubspotutk=abff935bba6e41e01231c115ed358579; __hssrc=1; _lfa=LF1.1.00fe1c25170ae096.1758180289865; cookieyes-consent=consentid:Qks5aERydjg4NUYwVnY5V3ptOUp6blY1M0hUYVc2TVc,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes; _ga=GA1.1.1486272837.1758180290; _gcl_au=1.1.2025724784.1758180290; _fbp=fb.1.1758180290201.476671445508456298; FPAU=1.1.2025724784.1758180290; dd_anonymous_id=3bdf2d32-82ce-4399-b251-af60c049a4d2; _clck=yta4sc%5E2%5Efzf%5E0%5E2087; _rdt_uuid=1758180290952.ccfb6b37-661a-4e09-a982-9b99214516ce; _ga_NCP2435BFQ=GS2.1.s1758180290$o1$g1$t1758180326$j24$l0$h127181621; _uetvid=90855b60946011f0b39e91c45e06f15c; auth=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhaWtpZG8uZGV2IiwiYXVkIjoidXNlcnMuYWlraWRvIiwiaWF0IjoxNzU4MjY3MzQwLCJuYmYiOjE3NTgyNjczMzAsImV4cCI6MTc1ODMzOTM0MCwidXNlcl9pZCI6NzU1NjV9.pEbEy_7t2taARm6THnP_ZVQOL1DKGKHpOB89PBLpjRA; intercom-session-j0dzii6j=NW1wVjVNSzJxaStOQXdLVHliNUJzZ3kxMi9ma2Z4MCt1ajhjWkF5RVBoT1ZHcWxneXFZaXNTRng3b0ZCWUd5eDNndzd4L0ZtUWVXWlJQZzErU2tTb1U0SnRjVGs2MHdvVzZYbkdYb3owLzA9LS13MXRTcmM4T3ZkWjVZbTh3ZjVOLzVBPT0=--d3bce553c8e41148920253bf716be6736738e022',
        'X-Group-Id': '38639'
    }

    
    page = start_page
    consecutive_failures = 0
    
    while True:
        with lock:
            if shared_failures.value >= 3:
                break
        
        # 检查文件是否已存在
        filename = os.path.join(output_dir, f"page_{page:04d}.json")
        if os.path.exists(filename):
            print(f"进程 {process_id}: 页面 {page} 已存在，跳过")
            page += step
            continue
            
        params = {
            'page': page,
            'search': '',
            'status': 'MALWARE'
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # 保存数据
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"进程 {process_id}: 页面 {page} 保存完成")
                consecutive_failures = 0
                with lock:
                    shared_failures.value = 0  # 重置全局失败计数
                
            else:
                consecutive_failures += 1
                with lock:
                    shared_failures.value += 1
                print(f"进程 {process_id}: 页面 {page} 请求失败，状态码: {response.status_code}")
                
        except Exception as e:
            consecutive_failures += 1
            with lock:
                shared_failures.value += 1
            print(f"进程 {process_id}: 页面 {page} 请求异常: {e}")
        
        page += step
        time.sleep(0.1)

def main():
    """主函数"""
    processes = []
    shared_failures = Value('i', 0)
    lock = Lock()
    
    # 启动30个进程
    for i in range(30):
        p = Process(target=crawl_pages, args=(i, i, 30, shared_failures, lock))
        p.start()
        processes.append(p)
    
    # 等待所有进程完成
    for p in processes:
        p.join()
    
    print("所有进程完成")

if __name__ == "__main__":
    main()