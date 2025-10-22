"""
任务日志记录器 - 用于记录和追踪 Pipeline 执行情况
可视化监控的数据来源，不影响原有业务逻辑
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, DESCENDING
import uuid


class TaskLogger:
    """Pipeline 任务执行日志记录器"""
    
    def __init__(self, connection_string: str = None):
        """初始化任务日志记录器"""
        if connection_string is None:
            connection_string = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
        
        self.client = MongoClient(connection_string)
        self.db = self.client.intelliradar
        self.tasks = self.db.pipeline_tasks
        
        # 创建索引
        self._create_indexes()
    
    def _create_indexes(self):
        """创建索引以优化查询性能"""
        self.tasks.create_index([("start_time", DESCENDING)])
        self.tasks.create_index([("status", 1)])
        self.tasks.create_index([("task_type", 1)])
        self.tasks.create_index([("task_id", 1)], unique=True)
    
    def create_task(self, task_type: str = "manual", trigger_source: str = "manual", 
                    sources: List[str] = None, workers: int = 3) -> str:
        """
        创建新的任务记录
        
        Args:
            task_type: 任务类型 (scheduled/manual/full)
            trigger_source: 触发源 (cron/api/manual/cli)
            sources: 要采集的源列表，None表示全部
            workers: 并发工作线程数
            
        Returns:
            task_id: 任务ID
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        task_doc = {
            "task_id": task_id,
            "task_type": task_type,
            "trigger_source": trigger_source,
            "start_time": datetime.now(),
            "end_time": None,
            "status": "running",
            "workers": workers,
            "sources_to_run": sources,  # None 表示全部
            
            # 初始化统计
            "total_sources": 0,
            "success_sources": 0,
            "failed_sources": 0,
            "total_duration": 0,
            
            # 每个source的详细结果
            "source_results": [],
            
            # 合并任务结果
            "merger_result": None,
            
            # 源代码收集结果
            "collector_result": None,
            
            # 下载详细日志
            "download_logs": [],
            
            # 元数据
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        self.tasks.insert_one(task_doc)
        print(f"📝 任务日志已创建: {task_id}")
        return task_id
    
    def update_crawler_results(self, task_id: str, results: List[Dict]):
        """
        更新爬虫执行结果
        
        Args:
            task_id: 任务ID
            results: 爬虫执行结果列表
        """
        source_results = []
        success_count = 0
        failed_count = 0
        
        for result in results:
            source_result = {
                "source": result.get('source', 'unknown'),
                "status": result.get('status', 'unknown'),
                "start_time": None,  # 单个source的开始时间（如果有的话）
                "end_time": None,
                "links_discovered": result.get('links_discovered', 0),
                "links_processed": result.get('links_processed', 0),
                "content_saved": result.get('content_saved', 0),
                "links_failed": result.get('links_failed', 0),
                "duration": result.get('duration', 0),
                "error": result.get('error', None),
                "pipeline_mode": result.get('pipeline_mode', True)
            }
            source_results.append(source_result)
            
            if result.get('status') == 'success':
                success_count += 1
            else:
                failed_count += 1
        
        self.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "source_results": source_results,
                    "total_sources": len(results),
                    "success_sources": success_count,
                    "failed_sources": failed_count,
                    "updated_at": datetime.now()
                }
            }
        )
        print(f"📝 任务 {task_id} 爬虫结果已更新: {success_count}/{len(results)} 成功")
    
    def update_merger_result(self, task_id: str, merged_count: int, 
                            confidence_stats: Dict = None, error: str = None):
        """
        更新合并任务结果
        
        Args:
            task_id: 任务ID
            merged_count: 合并的情报数量
            confidence_stats: 置信度统计
            error: 错误信息（如果有）
        """
        merger_result = {
            "status": "success" if error is None else "failed",
            "merged_count": merged_count,
            "confidence_stats": confidence_stats or {},
            "error": error,
            "timestamp": datetime.now()
        }
        
        self.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "merger_result": merger_result,
                    "updated_at": datetime.now()
                }
            }
        )
        print(f"📝 任务 {task_id} 合并结果已更新: {merged_count} 个情报包")
    
    def update_collector_result(self, task_id: str, stats: Dict, error: str = None):
        """
        更新源代码收集结果
        
        Args:
            task_id: 任务ID
            stats: 收集统计信息
            error: 错误信息（如果有）
        """
        collector_result = {
            "status": "success" if error is None else "failed",
            "total_packages": stats.get('total_in_db', 0),
            "pypi_npm_count": stats.get('pypi_npm_count', 0),
            "already_collected": stats.get('already_collected', 0),
            "need_collect": stats.get('need_collect', 0),
            "collect_success": stats.get('collect_success', 0),
            "collect_failed": stats.get('collect_failed', 0),
            "other_managers": stats.get('other_managers', 0),
            "error": error,
            "timestamp": datetime.now()
        }
        
        self.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "collector_result": collector_result,
                    "updated_at": datetime.now()
                }
            }
        )
        
        success_count = stats.get('collect_success', 0)
        total_count = stats.get('need_collect', 0)
        print(f"📝 任务 {task_id} 源代码收集结果已更新: {success_count}/{total_count} 成功")
    
    def add_download_log(self, task_id: str, package_manager: str, package_name: str, 
                        version: str, status: str, file_path: str = None, 
                        mirror: str = None, error: str = None):
        """
        添加单个包下载日志
        
        Args:
            task_id: 任务ID
            package_manager: 包管理器 (pypi/npm)
            package_name: 包名
            version: 版本号
            status: 下载状态 (success/failed/skipped)
            file_path: 下载文件路径
            mirror: 使用的镜像源
            error: 错误信息（如果有）
        """
        log_entry = {
            "package_manager": package_manager,
            "package_name": package_name,
            "version": version,
            "status": status,
            "file_path": file_path,
            "mirror": mirror,
            "error": error,
            "timestamp": datetime.now()
        }
        
        self.tasks.update_one(
            {"task_id": task_id},
            {
                "$push": {"download_logs": log_entry},
                "$set": {"updated_at": datetime.now()}
            }
        )
    
    def complete_task(self, task_id: str, status: str = "completed"):
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            status: 最终状态 (completed/failed)
        """
        task = self.tasks.find_one({"task_id": task_id})
        if task:
            end_time = datetime.now()
            duration = (end_time - task['start_time']).total_seconds()
            
            self.tasks.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": status,
                        "end_time": end_time,
                        "total_duration": duration,
                        "updated_at": end_time
                    }
                }
            )
            print(f"✅ 任务 {task_id} 已完成，耗时 {duration:.2f}s")
    
    def fail_task(self, task_id: str, error: str):
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
        """
        self.tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": "failed",
                    "end_time": datetime.now(),
                    "error": error,
                    "updated_at": datetime.now()
                }
            }
        )
        print(f"❌ 任务 {task_id} 失败: {error}")
    
    # ========== 查询方法（供前端API使用）==========
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取单个任务详情"""
        return self.tasks.find_one({"task_id": task_id}, {"_id": 0})
    
    def get_latest_tasks(self, limit: int = 20) -> List[Dict]:
        """获取最近的任务列表"""
        return list(self.tasks.find(
            {},
            {"_id": 0}
        ).sort("start_time", DESCENDING).limit(limit))
    
    def get_tasks_by_date(self, date: str) -> List[Dict]:
        """
        获取指定日期的任务
        
        Args:
            date: 日期字符串 'YYYY-MM-DD'
        """
        start = datetime.strptime(date, '%Y-%m-%d')
        end = datetime.strptime(date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        return list(self.tasks.find(
            {
                "start_time": {
                    "$gte": start,
                    "$lte": end
                }
            },
            {"_id": 0}
        ).sort("start_time", DESCENDING))
    
    def get_running_tasks(self) -> List[Dict]:
        """获取当前正在运行的任务"""
        return list(self.tasks.find(
            {"status": "running"},
            {"_id": 0}
        ).sort("start_time", DESCENDING))
    
    def get_task_statistics(self, days: int = 7) -> Dict:
        """
        获取任务统计信息
        
        Args:
            days: 统计最近几天的数据
        """
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        tasks = list(self.tasks.find({
            "start_time": {"$gte": start_date}
        }))
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
        failed_tasks = len([t for t in tasks if t['status'] == 'failed'])
        running_tasks = len([t for t in tasks if t['status'] == 'running'])
        
        total_sources_crawled = sum(t.get('total_sources', 0) for t in tasks)
        total_success_sources = sum(t.get('success_sources', 0) for t in tasks)
        total_failed_sources = sum(t.get('failed_sources', 0) for t in tasks)
        
        total_intelligence = sum(
            t.get('merger_result', {}).get('merged_count', 0) 
            for t in tasks if t.get('merger_result')
        )
        
        # 源代码收集统计
        total_packages_collected = sum(
            t.get('collector_result', {}).get('collect_success', 0)
            for t in tasks if t.get('collector_result')
        )
        
        return {
            "period_days": days,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "success_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
            
            "total_sources_crawled": total_sources_crawled,
            "total_success_sources": total_success_sources,
            "total_failed_sources": total_failed_sources,
            "source_success_rate": round(total_success_sources / total_sources_crawled * 100, 2) if total_sources_crawled > 0 else 0,
            
            "total_intelligence_merged": total_intelligence,
            "total_packages_collected": total_packages_collected,
            
            "latest_task": tasks[0] if tasks else None
        }
    
    def get_source_performance(self, days: int = 30) -> List[Dict]:
        """
        获取各个源的性能统计
        
        Args:
            days: 统计最近几天的数据
        """
        from datetime import timedelta
        from collections import defaultdict
        
        start_date = datetime.now() - timedelta(days=days)
        
        tasks = list(self.tasks.find({
            "start_time": {"$gte": start_date},
            "status": {"$in": ["completed", "failed"]}
        }))
        
        # 按source聚合统计
        source_stats = defaultdict(lambda: {
            "total_runs": 0,
            "success_runs": 0,
            "failed_runs": 0,
            "total_links": 0,
            "total_content": 0,
            "total_duration": 0,
            "avg_duration": 0
        })
        
        for task in tasks:
            for source_result in task.get('source_results', []):
                source = source_result['source']
                stats = source_stats[source]
                
                stats['total_runs'] += 1
                if source_result['status'] == 'success':
                    stats['success_runs'] += 1
                else:
                    stats['failed_runs'] += 1
                
                stats['total_links'] += source_result.get('links_discovered', 0)
                stats['total_content'] += source_result.get('content_saved', 0)
                stats['total_duration'] += source_result.get('duration', 0)
        
        # 计算平均值和成功率
        result = []
        for source, stats in source_stats.items():
            stats['success_rate'] = round(stats['success_runs'] / stats['total_runs'] * 100, 2) if stats['total_runs'] > 0 else 0
            stats['avg_duration'] = round(stats['total_duration'] / stats['total_runs'], 2) if stats['total_runs'] > 0 else 0
            stats['avg_links'] = round(stats['total_links'] / stats['success_runs'], 2) if stats['success_runs'] > 0 else 0
            
            result.append({
                "source": source,
                **stats
            })
        
        # 按成功率排序
        result.sort(key=lambda x: x['success_rate'], reverse=True)
        return result
    
    def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()

