"""
IntelliRadar API Models
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Annotated, Union
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from bson import ObjectId


# 简化的 ObjectId 处理
PyObjectId = Annotated[str, Field(...)]


# ============= 威胁情报相关模型 =============

class Source(BaseModel):
    """威胁情报来源"""
    discoverer: Union[List[str], str]
    data_source: str
    discovery_date: datetime
    source_link: str


class Credit(BaseModel):
    """威胁情报信用信息"""
    sources: List[Source]
    collected_at: datetime


class Reference(BaseModel):
    """参考链接"""
    url: str
    type: str


class ThreatInfo(BaseModel):
    """威胁信息"""
    attack_methods: List[str] = []
    attack_vectors: List[str] = []
    targets: List[str] = []


class PatchInfo(BaseModel):
    """补丁信息"""
    fix_method: str
    patch_available: bool = False
    patch_url: Optional[str] = None


class Metadata(BaseModel):
    """元数据"""
    created_at: datetime
    last_updated: datetime
    data_quality_score: float
    confidence_level: str


class ThreatIntelligence(BaseModel):
    """威胁情报主模型"""
    id: Optional[str] = Field(default=None, alias="_id")
    threat_id: str = Field(..., alias="id")
    package_name: str
    package_manager: str
    package_versions: Union[List[str], str] = []
    repository_url: List[str] = []
    credit: Credit
    references: List[Reference] = []
    threat_info: ThreatInfo
    patch_info: Optional[PatchInfo] = None
    indicators_of_compromise: List[str] = []
    metadata: Metadata

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        str_strip_whitespace=True
    )


# ============= 用户管理相关模型 =============

class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """数据库中的用户模型"""
    id: Optional[str] = Field(default=None, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class User(UserBase):
    """返回给客户端的用户模型"""
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None


class Token(BaseModel):
    """访问令牌"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """令牌数据"""
    username: Optional[str] = None


# ============= API响应模型 =============

class ThreatListResponse(BaseModel):
    """威胁列表响应"""
    threats: List[ThreatIntelligence]
    total: int
    page: int
    page_size: int
    total_pages: int


class SearchQuery(BaseModel):
    """搜索查询参数"""
    query: Optional[str] = None
    package_manager: Optional[str] = None
    confidence_level: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    attack_methods: Optional[List[str]] = None


class PackageQuery(BaseModel):
    """包查询参数"""
    package_name: str = Field(..., description="包名称（必需）")
    package_manager: str = Field(..., description="包管理器（必需）")
    package_versions: Optional[str] = Field(None, description="包版本（可选）")


class StatisticsResponse(BaseModel):
    """统计信息响应"""
    total_threats: int
    package_managers: List[Dict[str, Any]]
    confidence_distribution: Dict[str, int]
    recent_updates: List[Dict[str, Any]]  # 简化为字典避免嵌套验证问题
    data_sources: List[Dict[str, Any]]  # 添加数据源统计
    monthly_trends: Optional[List[Dict[str, Any]]] = []  # 设为可选


class APIResponse(BaseModel):
    """通用API响应"""
    success: bool
    message: str
    data: Optional[Any] = None


# ============= 分页模型 =============

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SortParams(BaseModel):
    """排序参数"""
    sort_by: str = "metadata.last_updated"
    sort_order: Annotated[str, Field(default="desc", pattern="^(asc|desc)$")]
