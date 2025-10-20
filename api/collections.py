"""
Collections API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from models.database import get_db
from models.schemas import CollectionCreate, CollectionUpdate, CollectionResponse
from services.collection_service import CollectionService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[CollectionResponse])
async def get_collections(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all collections with optional filtering"""
    try:
        service = CollectionService(db)
        collections = service.get_collections(status=status, limit=limit, offset=offset)
        return collections
    except Exception as e:
        logger.error(f"Error getting collections: {e}")
        raise HTTPException(status_code=500, detail="Failed to get collections")

@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific collection by ID"""
    try:
        service = CollectionService(db)
        collection = service.get_collection_by_id(collection_id)
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        return collection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get collection")

@router.post("/", response_model=CollectionResponse)
async def create_collection(
    collection: CollectionCreate,
    db: Session = Depends(get_db)
):
    """Create a new collection"""
    try:
        service = CollectionService(db)
        new_collection = service.create_collection(collection)
        return new_collection
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to create collection")

@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    collection: CollectionUpdate,
    db: Session = Depends(get_db)
):
    """Update a collection"""
    try:
        service = CollectionService(db)
        updated_collection = service.update_collection(collection_id, collection)
        if not updated_collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        return updated_collection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collection {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update collection")

@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    db: Session = Depends(get_db)
):
    """Delete a collection"""
    try:
        service = CollectionService(db)
        success = service.delete_collection(collection_id)
        if not success:
            raise HTTPException(status_code=404, detail="Collection not found")
        return {"message": "Collection deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete collection")

@router.post("/{collection_id}/archive")
async def archive_collection(
    collection_id: str,
    db: Session = Depends(get_db)
):
    """Archive a collection"""
    try:
        service = CollectionService(db)
        success = service.archive_collection(collection_id)
        if not success:
            raise HTTPException(status_code=404, detail="Collection not found")
        return {"message": "Collection archived successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving collection {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive collection")

@router.post("/{collection_id}/unarchive")
async def unarchive_collection(
    collection_id: str,
    db: Session = Depends(get_db)
):
    """Unarchive a collection"""
    try:
        service = CollectionService(db)
        success = service.unarchive_collection(collection_id)
        if not success:
            raise HTTPException(status_code=404, detail="Collection not found")
        return {"message": "Collection unarchived successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unarchiving collection {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to unarchive collection")

@router.get("/{collection_id}/stats")
async def get_collection_stats(
    collection_id: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a collection"""
    try:
        service = CollectionService(db)
        stats = service.get_collection_stats(collection_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Collection not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection stats {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get collection statistics")
