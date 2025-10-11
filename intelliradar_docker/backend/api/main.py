"""
IntelliRadar FastAPI Main Application
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uvicorn
import os
from pydantic import ValidationError

from .models import (
    ThreatIntelligence, ThreatListResponse, SearchQuery, PackageQuery,
    User, UserRegisterRequest, UserInDB, Token, APIResponse,
    PaginationParams, SortParams
)
from .database import db_manager
from .auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, get_optional_current_user
)
from .task_monitor_api import router as task_monitor_router  # 任务监控 API
from loguru import logger

MAX_FREE_ITEMS = int(os.getenv("FREE_USER_MAX_ITEMS", "200"))  # 未登录用户最多查看200条
DEFAULT_AUTH_VIEW_LIMIT = int(os.getenv("DEFAULT_USER_VIEW_LIMIT", "500"))  # 登录用户默认500条

# Create FastAPI application
app = FastAPI(
    title="IntelliRadar API",
    description="Malicious Package Manager Component Threat Intelligence Database API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000", "http://27.54.47.51:6443", "http://localhost:6443"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(task_monitor_router)  # 任务监控路由

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on application startup"""
    try:
        await db_manager.connect_async()
        logger.info("IntelliRadar API started successfully")
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown"""
    await db_manager.close_async()
    logger.info("IntelliRadar API has been closed")


# ============= Authentication APIs =============

@app.post("/api/auth/register", response_model=APIResponse)
async def register(user: UserRegisterRequest):
    """User registration"""
    try:
        email = user.email.strip().lower()
        view_limit = user.view_limit or DEFAULT_AUTH_VIEW_LIMIT
        if view_limit <= 0:
            view_limit = DEFAULT_AUTH_VIEW_LIMIT

        # Check if username already exists
        existing_user = await db_manager.get_user_by_username(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account already exists"
            )
        
        existing_email = await db_manager.get_user_by_email(email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = get_password_hash(user.password)
        user_data = {
            "username": email,
            "email": email,
            "full_name": user.full_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "view_limit": view_limit
        }
        
        user_id = await db_manager.create_user(user_data)
        
        return APIResponse(
            success=True,
            message="User registered successfully",
            data={"user_id": str(user_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred during registration"
        )


@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    """User login"""
    identifier = form_data.username.strip().lower()
    user = await authenticate_user(identifier, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Update last login time
    await db_manager.update_user_login_time(user.username, datetime.now(timezone.utc))
    
    # Record login history
    client_ip = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    await db_manager.record_login_history(user.username, client_ip, user_agent)
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """
    Refresh access token (sliding expiration)
    Each API call can refresh the token to extend the session
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


# ============= Threat Intelligence APIs =============

@app.get("/api/threats", response_model=ThreatListResponse)
async def get_threats(
    pagination: PaginationParams = Depends(),
    sort: SortParams = Depends(),
    package_manager: Optional[str] = None,
    confidence_level: Optional[str] = None,
    package_name: Optional[str] = None,
    data_source: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: Optional[UserInDB] = Depends(get_optional_current_user)
):
    """Get threat intelligence list"""
    print("=== GET_THREATS FUNCTION CALLED ===")
    try:
        # Build filter conditions
        filter_dict = {}
        if package_manager:
            # 不区分大小写的正则匹配
            filter_dict["package_manager"] = {"$regex": f"^{package_manager}$", "$options": "i"}
        if confidence_level:
            # 不区分大小写的正则匹配
            filter_dict["metadata.confidence_level"] = {"$regex": f"^{confidence_level}$", "$options": "i"}
        if package_name:
            # 包名支持模糊匹配，不区分大小写
            filter_dict["package_name"] = {"$regex": package_name, "$options": "i"}
        if data_source:
            # 不区分大小写的正则匹配
            filter_dict["credit.sources.data_source"] = {"$regex": f"^{data_source}$", "$options": "i"}
        
        # Handle date range filtering
        if date_from or date_to:
            date_filter = {}
            if date_from:
                try:
                    from datetime import datetime
                    date_filter["$gte"] = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                except:
                    pass
            if date_to:
                try:
                    from datetime import datetime
                    date_filter["$lte"] = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                except:
                    pass
            if date_filter:
                filter_dict["metadata.last_updated"] = date_filter
        
        # Build sort conditions
        sort_order = -1 if sort.sort_order == "desc" else 1
        sort_dict = {sort.sort_by: sort_order}
        
        # Calculate pagination parameters and access limits
        skip = (pagination.page - 1) * pagination.page_size
        
        # Determine user's access limit
        if current_user:
            # 登录用户：使用view_limit字段
            user_limit = current_user.view_limit or DEFAULT_AUTH_VIEW_LIMIT
            max_allowed_total = user_limit
        else:
            # 未登录用户：最多200条
            user_limit = MAX_FREE_ITEMS
            max_allowed_total = MAX_FREE_ITEMS
        
        # Check if user has exceeded their limit
        if skip >= user_limit:
            if current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You have reached your viewing limit ({user_limit} items). Upgrade your account for more access."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Login required to view more than {MAX_FREE_ITEMS} items. Please sign in or register."
                )
        
        # Calculate effective limit for this page
        remaining = user_limit - skip
        effective_limit = min(pagination.page_size, remaining)
        
        if effective_limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have reached the viewing limit for your account."
            )
        
        # Query data
        print("MAIN: About to call get_threats_paginated")
        threats, total = await db_manager.get_threats_paginated(
            skip=skip,
            limit=effective_limit,
            filter_dict=filter_dict,
            sort_dict=sort_dict
        )
        
        print(f"MAIN: Got {len(threats)} threats from database")
        if threats:
            print(f"MAIN: First threat keys: {threats[0].keys()}")
            print(f"MAIN: First threat _id type: {type(threats[0].get('_id'))}")
            print(f"MAIN: First threat package_versions type: {type(threats[0].get('package_versions'))}")
        
        # Calculate total pages
        permitted_total = min(total, max_allowed_total)
        total_pages = (permitted_total + pagination.page_size - 1) // pagination.page_size if permitted_total else 0
        
        print("MAIN: About to create ThreatIntelligence objects")
        valid_threats = []
        skipped = 0
        for threat in threats:
            try:
                valid_threats.append(ThreatIntelligence(**threat))
            except ValidationError as ve:
                skipped += 1
                logger.warning(
                    "Skipping threat record due to validation error | id={} | error={}",
                    threat.get("id") or threat.get("mongo_id") or threat.get("_id"),
                    ve.errors(),
                )
            except Exception as ve:
                skipped += 1
                logger.warning(
                    "Skipping threat record due to unexpected error | id={} | error={}",
                    threat.get("id") or threat.get("mongo_id") or threat.get("_id"),
                    ve,
                )

        adjusted_total = max(permitted_total - skipped, 0)
        response_total = adjusted_total

        return ThreatListResponse(
            threats=valid_threats,
            total=response_total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages if skipped == 0 else (adjusted_total + pagination.page_size - 1) // pagination.page_size if adjusted_total else 0
        )
        
    except Exception as e:
        logger.error(f"Failed to get threat intelligence list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get threat intelligence"
        )


@app.get("/api/threats/latest")
async def get_latest_threats():
    """Get latest 10 malicious packages"""
    try:
        logger.info("Getting latest threats...")
        # Get latest 10 threats sorted by last_updated or created_at
        threats = await db_manager.get_latest_threats(limit=10)
        logger.info(f"Found {len(threats)} threats")
        
        # Format the response for homepage display
        latest_packages = []
        for threat in threats:
            package_info = {
                "id": str(threat.get("_id")),
                "package_name": threat.get("package_name", "Unknown"),
                "package_manager": threat.get("package_manager", "Unknown"),
                "version": threat.get("package_versions", ["Unknown"]) if threat.get("package_versions") else ["Unknown"],
                "collected_time": threat.get("metadata", {}).get("last_updated") or threat.get("metadata", {}).get("created_at"),
                "confidence_level": threat.get("metadata", {}).get("confidence_level", "unknown")
            }
            latest_packages.append(package_info)
        
        return JSONResponse(content={"latest_packages": latest_packages})
        
    except Exception as e:
        logger.error(f"Failed to get latest threats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get latest threats"
        )


@app.get("/api/threats/{threat_id}", response_model=ThreatIntelligence)
async def get_threat_detail(threat_id: str):
    """Get threat intelligence details"""
    try:
        threat = await db_manager.get_threat_by_id(threat_id)
        if not threat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Threat intelligence not found"
            )
        
        return ThreatIntelligence(**threat)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get threat intelligence details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get threat intelligence details"
        )


@app.post("/api/threats/search", response_model=List[ThreatIntelligence])
async def search_threats(
    search_query: SearchQuery,
    current_user: Optional[UserInDB] = Depends(get_optional_current_user)
):
    """Search threat intelligence"""
    try:
        # Build search filter conditions
        filters = {}
        
        if search_query.package_manager:
            # 不区分大小写的正则匹配
            filters["package_manager"] = {"$regex": f"^{search_query.package_manager}$", "$options": "i"}
        
        if search_query.confidence_level:
            # 不区分大小写的正则匹配
            filters["metadata.confidence_level"] = {"$regex": f"^{search_query.confidence_level}$", "$options": "i"}
        
        if search_query.date_from or search_query.date_to:
            date_filter = {}
            if search_query.date_from:
                date_filter["$gte"] = search_query.date_from
            if search_query.date_to:
                date_filter["$lte"] = search_query.date_to
            filters["metadata.created_at"] = date_filter
        
        if search_query.attack_methods:
            filters["threat_info.attack_methods"] = {"$in": search_query.attack_methods}
        
        # Execute search
        raw_threats = await db_manager.search_threats(
            query=search_query.query,
            filters=filters
        )
        
        allowed_total = current_user.view_limit if current_user else MAX_FREE_PAGES * FREE_PAGE_SIZE
        if not allowed_total or allowed_total <= 0:
            allowed_total = DEFAULT_AUTH_VIEW_LIMIT
        
        threats = []
        for threat in raw_threats:
            if len(threats) >= allowed_total:
                break
            try:
                threats.append(ThreatIntelligence(**threat))
            except ValidationError as ve:
                logger.warning(
                    "Skipping threat in search results due to validation error | id={} | error={}",
                    threat.get("id") or threat.get("mongo_id") or threat.get("_id"),
                    ve.errors(),
                )
            except Exception as ve:
                logger.warning(
                    "Skipping threat in search results due to unexpected error | id={} | error={}",
                    threat.get("id") or threat.get("mongo_id") or threat.get("_id"),
                    ve,
                )
        
        return threats
        
    except Exception as e:
        logger.error(f"Failed to search threat intelligence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search threat intelligence"
        )


@app.post("/api/packages/query", response_model=List[ThreatIntelligence])
async def query_package_details(
    package_query: PackageQuery,
    current_user: Optional[UserInDB] = Depends(get_optional_current_user)
):
    """
    根据包名、包管理器和版本查询包的详细信息
    
    Args:
        package_query: 包查询参数，包含package_name（必需）、package_manager（必需）、package_versions（可选）
        
    Returns:
        匹配的威胁情报列表
        
    Notes:
        - package_name 和 package_manager 为必需参数
        - package_versions 为可选参数，如果未提供则返回所有匹配的包
        - 支持通配符版本匹配：如果数据库中的版本包含 *、[0,]、>= 0、[0,) 等，则匹配任何查询版本
        - 所有匹配都忽略大小写
        - 如果查询版本为 "0.0.1" 但数据库版本为 "*"，则匹配成功
    """
    try:
        logger.info(f"收到包查询请求: {package_query.package_name} ({package_query.package_manager}) 版本: {package_query.package_versions}")
        
        # 调用数据库查询方法
        threats = await db_manager.query_package_details(
            package_name=package_query.package_name,
            package_manager=package_query.package_manager,
            package_versions=package_query.package_versions
        )
        
        if not threats:
            logger.info(f"未找到匹配的包: {package_query.package_name} ({package_query.package_manager})")
            return []
        
        logger.info(f"找到 {len(threats)} 个匹配的威胁情报记录")
        
        # 转换为ThreatIntelligence对象并返回
        threat_objects = []
        for threat in threats:
            try:
                threat_obj = ThreatIntelligence(**threat)
                threat_objects.append(threat_obj)
            except Exception as e:
                logger.error(f"转换威胁情报对象失败: {e}, 原始数据: {threat}")
                continue
        
        allowed_total = current_user.view_limit if current_user else MAX_FREE_PAGES * FREE_PAGE_SIZE
        if not allowed_total or allowed_total <= 0:
            allowed_total = DEFAULT_AUTH_VIEW_LIMIT
        
        return threat_objects[:allowed_total]
        
    except Exception as e:
        logger.error(f"查询包详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询包详情失败: {str(e)}"
        )


@app.get("/api/statistics")
async def get_statistics():
    """Get statistics information"""
    try:
        stats = await db_manager.get_statistics()
        # 使用JSONResponse直接返回，完全绕过Pydantic验证
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )


# ============= Health Check APIs =============

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}


@app.get("/")
async def root():
    """Root path"""
    return {"message": "IntelliRadar API is running", "docs": "/api/docs"}


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
