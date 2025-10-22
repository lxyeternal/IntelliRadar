"""
Pipeline 任务监控 API
提供任务执行历史、状态查询等功能，用于前端可视化
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from database.task_logger import TaskLogger

router = APIRouter(prefix="/api/tasks", tags=["Task Monitor"])


@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """
    获取仪表盘汇总信息（今天、昨天、本周）
    前端调用：axios.get('/api/tasks/dashboard/summary')
    """
    task_logger = TaskLogger()
    try:
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        week_start = today_start - timedelta(days=7)
        
        # 今天的任务
        today_tasks = list(task_logger.tasks.find({
            "start_time": {"$gte": today_start}
        }))
        
        # 昨天的任务
        yesterday_tasks = list(task_logger.tasks.find({
            "start_time": {"$gte": yesterday_start, "$lt": today_start}
        }))
        
        # 本周的任务
        week_tasks = list(task_logger.tasks.find({
            "start_time": {"$gte": week_start}
        }))
        
        def calculate_summary(tasks):
            """计算任务汇总信息"""
            total = len(tasks)
            completed = len([t for t in tasks if t['status'] == 'completed'])
            failed = len([t for t in tasks if t['status'] == 'failed'])
            running = len([t for t in tasks if t['status'] == 'running'])
            
            total_sources = sum(t.get('total_sources', 0) for t in tasks)
            success_sources = sum(t.get('success_sources', 0) for t in tasks)
            
            total_intelligence = sum(
                t.get('merger_result', {}).get('merged_count', 0) 
                for t in tasks if t.get('merger_result')
            )
            
            total_links = 0
            total_content = 0
            for task in tasks:
                for sr in task.get('source_results', []):
                    total_links += sr.get('links_discovered', 0)
                    total_content += sr.get('content_saved', 0)
            
            # 找到最近完成的任务
            completed_tasks = [t for t in tasks if t['status'] == 'completed']
            last_completed = None
            if completed_tasks:
                last_completed = max(completed_tasks, key=lambda x: x.get('end_time', x['start_time']))
            
            return {
                "total_tasks": total,
                "completed_tasks": completed,
                "failed_tasks": failed,
                "running_tasks": running,
                "success_rate": round(completed / total * 100, 2) if total > 0 else 0,
                
                "total_sources": total_sources,
                "success_sources": success_sources,
                "source_success_rate": round(success_sources / total_sources * 100, 2) if total_sources > 0 else 0,
                
                "total_intelligence": total_intelligence,
                "total_links": total_links,
                "total_content": total_content,
                
                "last_completed_task": {
                    "task_id": last_completed.get('task_id'),
                    "end_time": last_completed.get('end_time').isoformat() if last_completed.get('end_time') else None,
                    "duration": last_completed.get('total_duration', 0)
                } if last_completed else None
            }
        
        return {
            "success": True,
            "data": {
                "today": calculate_summary(today_tasks),
                "yesterday": calculate_summary(yesterday_tasks),
                "week": calculate_summary(week_tasks),
                "current_running": len([t for t in today_tasks if t['status'] == 'running']) > 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        task_logger.close()


@router.get("/latest")
async def get_latest_tasks(limit: int = Query(10, ge=1, le=100)):
    """
    获取最近的任务列表
    前端调用：axios.get('/api/tasks/latest?limit=10')
    """
    task_logger = TaskLogger()
    try:
        tasks = task_logger.get_latest_tasks(limit=limit)
        return {
            "success": True,
            "data": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        task_logger.close()


@router.get("/running/current")
async def get_running_tasks():
    """
    获取当前正在运行的任务
    前端调用：axios.get('/api/tasks/running/current')
    """
    task_logger = TaskLogger()
    try:
        tasks = task_logger.get_running_tasks()
        return {
            "success": True,
            "data": tasks,
            "count": len(tasks),
            "has_running": len(tasks) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        task_logger.close()


@router.get("/statistics/sources")
async def get_source_performance(days: int = Query(30, ge=1, le=90)):
    """
    获取各个源的性能统计
    前端调用：axios.get('/api/tasks/statistics/sources?days=30')
    """
    task_logger = TaskLogger()
    try:
        performance = task_logger.get_source_performance(days=days)
        return {
            "success": True,
            "data": performance,
            "count": len(performance)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        task_logger.close()


@router.get("/{task_id}")
async def get_task_detail(task_id: str):
    """
    获取单个任务的详细信息
    前端调用：axios.get(`/api/tasks/${taskId}`)
    """
    task_logger = TaskLogger()
    try:
        task = task_logger.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return {
            "success": True,
            "data": task
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        task_logger.close()


@router.get("/by-date/{date}")
async def get_tasks_by_date(date: str):
    """
    获取指定日期的所有任务
    Args:
        date: 日期 (YYYY-MM-DD 格式)
    """
    task_logger = TaskLogger()
    try:
        # 验证日期格式
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        tasks = task_logger.get_tasks_by_date(date)
        return {
            "success": True,
            "date": date,
            "data": tasks,
            "count": len(tasks)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        task_logger.close()


@router.get("/statistics/overview")
async def get_task_statistics(days: int = Query(7, ge=1, le=90)):
    """
    获取任务统计信息
    Args:
        days: 统计最近几天的数据 (1-90)
    """
    task_logger = TaskLogger()
    try:
        stats = task_logger.get_task_statistics(days=days)
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        task_logger.close()

