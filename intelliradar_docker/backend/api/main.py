"""
IntelliRadar FastAPI Main Application
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uvicorn
import os

from .models import (
    ThreatIntelligence, ThreatListResponse, SearchQuery, 
    User, UserCreate, Token, APIResponse,
    PaginationParams, SortParams
)
from .database import db_manager
from .auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
from loguru import logger

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
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def register(user: UserCreate):
    """User registration"""
    try:
        # Check if username already exists
        existing_user = await db_manager.get_user_by_username(user.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        existing_email = await db_manager.get_user_by_email(user.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = get_password_hash(user.password)
        user_data = {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
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
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login"""
    user = await authenticate_user(form_data.username, form_data.password)
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
    date_to: Optional[str] = None
):
    """Get threat intelligence list"""
    print("=== GET_THREATS FUNCTION CALLED ===")
    try:
        # Build filter conditions
        filter_dict = {}
        if package_manager:
            filter_dict["package_manager"] = package_manager
        if confidence_level:
            filter_dict["metadata.confidence_level"] = confidence_level
        if package_name:
            filter_dict["package_name"] = {"$regex": package_name, "$options": "i"}
        if data_source:
            filter_dict["credit.sources.data_source"] = data_source
        
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
        
        # Calculate pagination parameters
        skip = (pagination.page - 1) * pagination.page_size
        
        # Query data
        print("MAIN: About to call get_threats_paginated")
        threats, total = await db_manager.get_threats_paginated(
            skip=skip,
            limit=pagination.page_size,
            filter_dict=filter_dict,
            sort_dict=sort_dict
        )
        
        print(f"MAIN: Got {len(threats)} threats from database")
        if threats:
            print(f"MAIN: First threat keys: {threats[0].keys()}")
            print(f"MAIN: First threat _id type: {type(threats[0].get('_id'))}")
            print(f"MAIN: First threat package_versions type: {type(threats[0].get('package_versions'))}")
        
        # Calculate total pages
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        print("MAIN: About to create ThreatIntelligence objects")
        return ThreatListResponse(
            threats=[ThreatIntelligence(**threat) for threat in threats],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Failed to get threat intelligence list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get threat intelligence"
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
async def search_threats(search_query: SearchQuery):
    """Search threat intelligence"""
    try:
        # Build search filter conditions
        filters = {}
        
        if search_query.package_manager:
            filters["package_manager"] = search_query.package_manager
        
        if search_query.confidence_level:
            filters["metadata.confidence_level"] = search_query.confidence_level
        
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
        threats = await db_manager.search_threats(
            query=search_query.query,
            filters=filters
        )
        
        return [ThreatIntelligence(**threat) for threat in threats]
        
    except Exception as e:
        logger.error(f"Failed to search threat intelligence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search threat intelligence"
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
