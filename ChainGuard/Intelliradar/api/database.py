"""
数据库连接和管理
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
import asyncio
from loguru import logger


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "intelliradar")
        default_user_db = self.database_name
        self.user_database_name = os.getenv("USER_DATABASE_NAME", default_user_db)
        
        # 异步客户端
        self.async_client: Optional[AsyncIOMotorClient] = None
        self.async_db = None
        self.async_user_db = None
        
        # 同步客户端（用于爬虫等同步操作）
        self.sync_client: Optional[MongoClient] = None
        self.sync_db = None
        self.sync_user_db = None

    async def connect_async(self):
        """建立异步连接"""
        try:
            self.async_client = AsyncIOMotorClient(self.mongodb_url)
            self.async_db = self.async_client[self.database_name]
            self.async_user_db = self.async_client[self.user_database_name]
            
            # 测试连接
            await self.async_client.admin.command('ping')
            logger.info(f"异步MongoDB连接成功: {self.mongodb_url}")
            
        except Exception as e:
            logger.error(f"异步MongoDB连接失败: {e}")
            raise

    def connect_sync(self):
        """建立同步连接"""
        try:
            self.sync_client = MongoClient(self.mongodb_url)
            self.sync_db = self.sync_client[self.database_name]
            self.sync_user_db = self.sync_client[self.user_database_name]
            
            # 测试连接
            self.sync_client.admin.command('ping')
            logger.info(f"同步MongoDB连接成功: {self.mongodb_url}")
            
        except Exception as e:
            logger.error(f"同步MongoDB连接失败: {e}")
            raise

    async def close_async(self):
        """关闭异步连接"""
        if self.async_client:
            self.async_client.close()
            logger.info("异步MongoDB连接已关闭")

    def close_sync(self):
        """关闭同步连接"""
        if self.sync_client:
            self.sync_client.close()
            logger.info("同步MongoDB连接已关闭")

    # ============= 威胁情报数据库操作 =============

    async def get_threats_collection(self):
        """获取威胁情报集合（异步）"""
        if self.async_db is None:
            await self.connect_async()
        return self.async_db.threat_intelligence

    def get_threats_collection_sync(self):
        """获取威胁情报集合（同步）"""
        if self.sync_db is None:
            self.connect_sync()
        return self.sync_db.threat_intelligence

    async def get_threat_by_id(self, threat_id: str):
        """根据ID获取威胁情报"""
        collection = await self.get_threats_collection()
        
        # 首先尝试使用自定义id字段查询
        threat = await collection.find_one({"id": threat_id})
        
        # 如果没找到，尝试使用MongoDB ObjectId查询
        if not threat:
            try:
                from bson import ObjectId
                if ObjectId.is_valid(threat_id):
                    threat = await collection.find_one({"_id": ObjectId(threat_id)})
            except Exception as e:
                print(f"Failed to query by ObjectId: {e}")
        
        if threat:
            # 处理数据格式 - 保留自定义id字段
            if '_id' in threat:
                # 如果没有自定义id字段，使用_id作为备选
                if 'id' not in threat or not threat['id']:
                    threat['id'] = str(threat['_id'])
                # 添加MongoDB的_id作为单独字段以备后用
                threat['mongo_id'] = str(threat['_id'])
                del threat['_id']
            
            # 处理package_versions字段
            if 'package_versions' in threat:
                if isinstance(threat['package_versions'], str):
                    try:
                        import json
                        parsed = json.loads(threat['package_versions'])
                        if isinstance(parsed, list):
                            threat['package_versions'] = parsed
                        else:
                            threat['package_versions'] = [str(parsed)]
                    except (json.JSONDecodeError, TypeError):
                        threat['package_versions'] = [threat['package_versions']]
                elif threat['package_versions'] is None:
                    threat['package_versions'] = []
        
        return threat

    async def get_threats_paginated(self, skip: int = 0, limit: int = 20, filter_dict: dict = None, sort_dict: dict = None):
        """分页获取威胁情报"""
        collection = await self.get_threats_collection()
        
        if filter_dict is None:
            filter_dict = {}
        
        if sort_dict is None:
            sort_dict = {"metadata.last_updated": -1}
        
        cursor = collection.find(filter_dict).sort(list(sort_dict.items())).skip(skip).limit(limit)
        threats = await cursor.to_list(length=limit)
        total = await collection.count_documents(filter_dict)
        
        # 处理数据格式，确保符合Pydantic模型要求
        processed_threats = []
        print(f"PROCESSING {len(threats)} THREATS")
        for i, threat in enumerate(threats):
            # 调试：打印原始数据类型
            print(f"THREAT {i}: _id type: {type(threat.get('_id'))}, value: {threat.get('_id')}")
            print(f"THREAT {i}: id field: {threat.get('id')}")
            print(f"THREAT {i}: package_versions type: {type(threat.get('package_versions'))}, value: {threat.get('package_versions')}")
            
            # 处理 _id 字段 - 保留自定义id字段，只在没有id字段时才使用_id
            if '_id' in threat:
                # 如果没有自定义id字段，使用_id作为备选
                if 'id' not in threat or not threat['id']:
                    threat['id'] = str(threat['_id'])
                # 添加MongoDB的_id作为单独字段以备后用
                threat['mongo_id'] = str(threat['_id'])
                del threat['_id']
                print(f"THREAT {i}: Using id: {threat.get('id')}, mongo_id: {threat.get('mongo_id')}")
            
            # 处理 package_versions 字段 - 处理混合格式（字符串和列表）
            if 'package_versions' in threat:
                if isinstance(threat['package_versions'], str):
                    # 尝试解析字符串格式的列表，如 "[1.0.7]" -> ["1.0.7"]
                    try:
                        import json
                        parsed = json.loads(threat['package_versions'])
                        if isinstance(parsed, list):
                            threat['package_versions'] = parsed
                        else:
                            threat['package_versions'] = [str(parsed)]
                    except (json.JSONDecodeError, TypeError):
                        # 如果解析失败，当作单个版本处理
                        threat['package_versions'] = [threat['package_versions']]
                elif threat['package_versions'] is None:
                    threat['package_versions'] = []
            
            processed_threats.append(threat)
        
        return processed_threats, total

    async def search_threats(self, query: str, filters: dict = None):
        """搜索威胁情报"""
        collection = await self.get_threats_collection()
        
        search_filter = {}
        
        if query:
            search_filter["$or"] = [
                {"package_name": {"$regex": query, "$options": "i"}},
                {"threat_info.attack_methods": {"$regex": query, "$options": "i"}},
                {"threat_info.attack_vectors": {"$regex": query, "$options": "i"}},
                {"indicators_of_compromise": {"$regex": query, "$options": "i"}}
            ]
        
        if filters:
            search_filter.update(filters)
        
        return await collection.find(search_filter).to_list(length=1000)

    async def get_latest_threats(self, limit: int = 10):
        """获取最新的威胁情报"""
        collection = await self.get_threats_collection()
        
        # 按照最后更新时间或创建时间排序，获取最新的威胁
        pipeline = [
            {
                "$addFields": {
                    "sort_date": {
                        "$ifNull": [
                            "$metadata.last_updated",
                            "$metadata.created_at"
                        ]
                    }
                }
            },
            {"$sort": {"sort_date": -1}},
            {"$limit": limit}
        ]
        
        threats = await collection.aggregate(pipeline).to_list(length=None)
        
        # 处理ObjectId和其他字段
        processed_threats = []
        for threat in threats:
            if threat.get('_id'):
                threat['_id'] = str(threat['_id'])
            processed_threats.append(threat)
        
        return processed_threats

    async def query_package_details(self, package_name: str, package_manager: str, package_versions: str = None):
        """
        根据包名、包管理器和版本查询包的详细信息
        
        Args:
            package_name: 包名（必需）
            package_manager: 包管理器（必需）
            package_versions: 包版本（可选）
            
        Returns:
            匹配的威胁情报列表
        """
        collection = await self.get_threats_collection()
        
        # 构建基础查询条件（忽略大小写）
        query = {
            "package_name": {"$regex": f"^{package_name}$", "$options": "i"},
            "package_manager": {"$regex": f"^{package_manager}$", "$options": "i"}
        }
        
        logger.info(f"查询包详情: {package_name} ({package_manager}) 版本: {package_versions}")
        
        # 获取所有匹配包名和包管理器的记录
        all_records = await collection.find(query).to_list(length=1000)
        
        if not all_records:
            logger.info(f"未找到匹配的包: {package_name} ({package_manager})")
            return []
        
        # 如果没有指定版本，返回所有记录
        if not package_versions:
            logger.info(f"未指定版本，返回所有 {len(all_records)} 条记录")
            return self._process_package_records(all_records)
        
        # 版本匹配逻辑
        matched_records = []
        target_version = str(package_versions).strip().lower()
        
        for record in all_records:
            db_versions = record.get('package_versions', [])
            
            # 直接将数据库版本数据转换为字符串
            if isinstance(db_versions, list):
                # 如果是列表，转换为字符串表示
                db_versions_str = str(db_versions).lower()
            else:
                # 如果是字符串或其他类型，直接转换为字符串
                db_versions_str = str(db_versions).lower()
            
            # 检查是否匹配
            version_matched = False
            
            # 检查是否包含全版本标识符
            if self._is_wildcard_version(db_versions_str):
                version_matched = True
                logger.info(f"匹配全版本模式: 数据库版本 '{db_versions_str}' 包含全版本标识符")
            # 检查输入版本是否在数据库版本字符串中
            elif target_version in db_versions_str:
                version_matched = True
                logger.info(f"版本匹配成功: 输入版本 '{target_version}' 在数据库版本 '{db_versions_str}' 中找到")
            
            if version_matched:
                matched_records.append(record)
        
        logger.info(f"版本匹配完成，找到 {len(matched_records)} 条匹配记录")
        return self._process_package_records(matched_records)
    
    def _is_wildcard_version(self, version_str: str) -> bool:
        """检查是否为通配符版本（表示所有版本）"""
        # 你提到的全版本模式
        all_version_patterns = {
            "*", ">= 0", "", "[0,)", ">=0", "> 0", 
            "[0,∞)", "all", "[0,]", "[*]"
        }
        
        # 额外的通配符模式
        additional_patterns = [
            "any", "*.*.*", "latest", "x.x.x"
        ]
        
        version_clean = version_str.strip().lower()
        
        # 检查精确匹配
        if version_clean in all_version_patterns:
            return True
            
        # 检查包含匹配
        return any(pattern in version_clean for pattern in additional_patterns)
    
    def _process_package_records(self, records):
        """处理包记录，确保格式正确"""
        processed_records = []
        for record in records:
            # 处理 _id 字段
            if '_id' in record:
                if 'id' not in record or not record['id']:
                    record['id'] = str(record['_id'])
                record['mongo_id'] = str(record['_id'])
                del record['_id']
            
            # 处理 package_versions 字段
            if 'package_versions' in record:
                if isinstance(record['package_versions'], str):
                    try:
                        import json
                        parsed = json.loads(record['package_versions'])
                        if isinstance(parsed, list):
                            record['package_versions'] = parsed
                        else:
                            record['package_versions'] = [str(parsed)]
                    except (json.JSONDecodeError, TypeError):
                        record['package_versions'] = [record['package_versions']]
                elif record['package_versions'] is None:
                    record['package_versions'] = []
            
            processed_records.append(record)
        
        return processed_records

    async def get_statistics(self):
        """获取统计信息"""
        collection = await self.get_threats_collection()
        
        # 基本统计
        total_threats = await collection.count_documents({})
        
        # 包管理器分布
        package_managers_pipeline = [
            {"$group": {"_id": "$package_manager", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]
        package_managers = await collection.aggregate(package_managers_pipeline).to_list(length=None)
        
        # 置信度分布
        confidence_pipeline = [
            {"$group": {"_id": "$metadata.confidence_level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        confidence_dist = await collection.aggregate(confidence_pipeline).to_list(length=None)
        confidence_distribution = {item["_id"]: item["count"] for item in confidence_dist}
        
        # 数据源分布
        data_sources_pipeline = [
            {"$unwind": "$credit.sources"},
            {"$group": {"_id": "$credit.sources.data_source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        data_sources = await collection.aggregate(data_sources_pipeline).to_list(length=None)
        
        # 最近更新 - 简化字段避免序列化问题
        recent_updates_cursor = collection.find(
            {},
            {"id": 1, "package_name": 1, "package_manager": 1, 
             "package_versions": 1, "metadata.last_updated": 1, "metadata.confidence_level": 1}
        ).sort("metadata.last_updated", -1).limit(10)
        recent_updates = await recent_updates_cursor.to_list(length=10)
        
        # 处理序列化问题
        for update in recent_updates:
            # 处理 _id 字段（转换为字符串）
            if '_id' in update:
                update['_id'] = str(update['_id'])
            
            # 处理 package_versions 字段 - 直接设为空列表避免序列化问题数据de
            if 'package_versions' in update:
                # 不管什么格式，统一设为空列表，避免序列化错误
                update['package_versions'] = []
            
            # 处理日期字段
            if 'metadata' in update and 'last_updated' in update['metadata']:
                if hasattr(update['metadata']['last_updated'], 'isoformat'):
                    update['metadata']['last_updated'] = update['metadata']['last_updated'].isoformat()
        
        # 月度趋势
        from datetime import datetime, timedelta
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        monthly_trends_pipeline = [
            {"$match": {"metadata.created_at": {"$gte": six_months_ago}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$metadata.created_at"},
                    "month": {"$month": "$metadata.created_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]
        monthly_trends = await collection.aggregate(monthly_trends_pipeline).to_list(length=None)
        
        # 处理monthly_trends数据，确保格式正确
        processed_monthly_trends = []
        for trend in monthly_trends:
            processed_monthly_trends.append({
                "year": trend["_id"]["year"],
                "month": trend["_id"]["month"], 
                "count": trend["count"]
            })
        
        # 今天发现的恶意组件数量
        from datetime import datetime, timezone
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_threats_count = await collection.count_documents({
            "metadata.created_at": {"$gte": today_start}
        })
        
        # 源代码收集统计
        # 统计有源代码的包数量（source_code.versions 字段存在且不为空）
        packages_with_source_count = await collection.count_documents({
            "source_code.versions": {"$exists": True, "$ne": {}}
        })
        
        # 统计总版本数（需要遍历所有有源代码的包）
        total_versions_pipeline = [
            {"$match": {"source_code.versions": {"$exists": True, "$ne": {}}}},
            {"$project": {
                "version_count": {"$size": {"$objectToArray": "$source_code.versions"}}
            }},
            {"$group": {
                "_id": None,
                "total_versions": {"$sum": "$version_count"}
            }}
        ]
        total_versions_result = await collection.aggregate(total_versions_pipeline).to_list(length=1)
        total_source_versions = total_versions_result[0]["total_versions"] if total_versions_result else 0
        
        return {
            "total_threats": total_threats,
            "package_managers": package_managers,
            "confidence_distribution": confidence_distribution,
            "recent_updates": recent_updates,
            "data_sources": data_sources,
            "monthly_trends": processed_monthly_trends,
            "today_threats_count": today_threats_count,
            "source_code_stats": {
                "packages_with_source": packages_with_source_count,
                "total_versions": total_source_versions
            }
        }

    # ============= 用户管理数据库操作 =============

    async def get_users_collection(self):
        """获取用户集合"""
        if self.async_user_db is None:
            await self.connect_async()
        return self.async_user_db.users

    async def get_sessions_collection(self):
        """获取会话集合"""
        if self.async_user_db is None:
            await self.connect_async()
        return self.async_user_db.sessions

    async def create_user(self, user_data: dict):
        """创建用户"""
        collection = await self.get_users_collection()
        if user_data.get("email"):
            user_data["email"] = user_data["email"].lower()
        if user_data.get("username"):
            user_data["username"] = user_data["username"].lower()
        user_data.setdefault("view_limit", 500)
        result = await collection.insert_one(user_data)
        return result.inserted_id

    async def get_user_by_username(self, username: str):
        """根据用户名获取用户"""
        collection = await self.get_users_collection()
        if username is None:
            return None
        user = await collection.find_one({"username": username.lower()})
        if user and "_id" in user:
            user["_id"] = str(user["_id"])
        return user

    async def get_user_by_email(self, email: str):
        """根据邮箱获取用户"""
        collection = await self.get_users_collection()
        if email is None:
            return None
        user = await collection.find_one({"email": email.lower()})
        if user and "_id" in user:
            user["_id"] = str(user["_id"])
        return user

    async def update_user_login_time(self, username: str, login_time):
        """更新用户最后登录时间"""
        collection = await self.get_users_collection()
        if not username:
            return
        await collection.update_one(
            {"username": username.lower()},
            {"$set": {"last_login": login_time}}
        )
    
    async def record_login_history(self, username: str, ip_address: str = None, user_agent: str = None):
        """记录用户登录历史"""
        from datetime import datetime, timezone
        collection = self.async_db.login_history
        login_record = {
            "username": username.lower(),
            "login_time": datetime.now(timezone.utc),
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        await collection.insert_one(login_record)
        # 创建索引
        await collection.create_index("username")
        await collection.create_index("login_time")

    async def create_session(self, session_data: dict):
        """创建会话"""
        collection = await self.get_sessions_collection()
        await collection.insert_one(session_data)

    async def get_session(self, token: str):
        """获取会话"""
        collection = await self.get_sessions_collection()
        return await collection.find_one({"token": token})

    async def delete_session(self, token: str):
        """删除会话"""
        collection = await self.get_sessions_collection()
        await collection.delete_one({"token": token})

    async def get_threat_trends(self, package_manager: str = None):
        """
        获取威胁发现趋势数据（按月统计，从2020年开始）
        
        Args:
            package_manager: 包管理器类型 (pypi/npm/nuget)，None 表示所有（不区分大小写）
            
        Returns:
            dict: 包含年月和数量的趋势数据
        """
        try:
            collection = await self.get_threats_collection()
            
            # 构建查询条件（不区分大小写）
            match_stage = {}
            if package_manager:
                # 使用正则表达式进行不区分大小写的匹配
                match_stage['package_manager'] = {
                    '$regex': f'^{package_manager}$',
                    '$options': 'i'
                }
            
            # 设置起始日期为 2020-01-01
            from datetime import datetime
            start_date = datetime(2020, 1, 1)
            
            # 聚合管道
            pipeline = []
            
            if match_stage:
                pipeline.append({'$match': match_stage})
            
            # 展开 credit.sources 数组
            pipeline.extend([
                {'$unwind': '$credit.sources'},
                {
                    '$addFields': {
                        'discovery_date_parsed': {
                            '$dateFromString': {
                                'dateString': '$credit.sources.discovery_date',
                                'onError': None,
                                'onNull': None
                            }
                        }
                    }
                },
                # 过滤掉解析失败的日期和早于2020年的数据
                {
                    '$match': {
                        'discovery_date_parsed': {
                            '$ne': None,
                            '$gte': start_date
                        }
                    }
                },
                # 按威胁 ID 分组，取最早的发现日期
                {
                    '$group': {
                        '_id': '$id',
                        'earliest_discovery': {'$min': '$discovery_date_parsed'},
                        'package_manager': {'$first': '$package_manager'}
                    }
                },
                # 按年月分组统计
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m',
                                'date': '$earliest_discovery'
                            }
                        },
                        'count': {'$sum': 1}
                    }
                },
                # 排序
                {'$sort': {'_id': 1}},
                # 重命名字段
                {
                    '$project': {
                        '_id': 0,
                        'date': '$_id',
                        'count': 1
                    }
                }
            ])
            
            result = await collection.aggregate(pipeline).to_list(None)
            
            # 填充缺失的月份（确保连续性）
            if result:
                date_counts = {item['date']: item['count'] for item in result}
                
                # 生成连续的年月列表（从2020-01到当前月份）
                current_month = start_date
                filled_data = []
                now = datetime.utcnow()
                
                while current_month <= now:
                    month_str = current_month.strftime('%Y-%m')
                    filled_data.append({
                        'date': month_str,
                        'count': date_counts.get(month_str, 0)
                    })
                    # 手动增加一个月
                    if current_month.month == 12:
                        current_month = current_month.replace(year=current_month.year + 1, month=1)
                    else:
                        current_month = current_month.replace(month=current_month.month + 1)
                
                return {
                    'trends': filled_data,
                    'package_manager': package_manager or 'all',
                    'period': 'monthly',
                    'start_date': '2020-01',
                    'total_threats': sum(item['count'] for item in filled_data)
                }
            else:
                return {
                    'trends': [],
                    'package_manager': package_manager or 'all',
                    'period': 'monthly',
                    'start_date': '2020-01',
                    'total_threats': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting threat trends: {e}")
            return {
                'trends': [],
                'package_manager': package_manager or 'all',
                'period': 'monthly',
                'start_date': '2020-01',
                'total_threats': 0
            }


# 全局数据库管理器实例
db_manager = DatabaseManager()
