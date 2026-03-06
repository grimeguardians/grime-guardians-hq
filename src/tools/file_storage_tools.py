"""
File Storage Tools
Handles photo uploads, document storage, and file management
Cloud storage integration for before/after photos and business documents
"""

import asyncio
import logging
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, BinaryIO
from pathlib import Path
import base64
import json

import aiofiles
from PIL import Image, ExifTags
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FileStorageError(Exception):
    """Custom file storage error."""
    pass


class FileValidator:
    """Validates file uploads for business requirements."""
    
    # Business file requirements
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
    ALLOWED_DOCUMENT_FORMATS = {'.pdf', '.doc', '.docx', '.txt'}
    
    @classmethod
    def validate_image(cls, file_path: Path, file_size: int) -> Dict[str, Any]:
        """Validate image file for business requirements."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        # Check file size
        if file_size > cls.MAX_FILE_SIZE:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"File size {file_size/1024/1024:.1f}MB exceeds limit of {cls.MAX_FILE_SIZE/1024/1024}MB")
        
        # Check file extension
        if file_path.suffix.lower() not in cls.ALLOWED_IMAGE_FORMATS:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"File format {file_path.suffix} not allowed. Allowed: {', '.join(cls.ALLOWED_IMAGE_FORMATS)}")
        
        # Validate image content
        try:
            with Image.open(file_path) as img:
                validation_result['metadata'] = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
                
                # Check minimum dimensions for quality photos
                if img.width < 800 or img.height < 600:
                    validation_result['warnings'].append("Image resolution is low - may affect quality assessment")
                
                # Check for EXIF data
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        for tag, value in exif.items():
                            tag_name = ExifTags.TAGS.get(tag, tag)
                            if tag_name == 'DateTime':
                                validation_result['metadata']['taken_at'] = value
                
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Invalid image file: {str(e)}")
        
        return validation_result
    
    @classmethod
    def validate_document(cls, file_path: Path, file_size: int) -> Dict[str, Any]:
        """Validate document file for business requirements."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        # Check file size
        if file_size > cls.MAX_FILE_SIZE:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"File size {file_size/1024/1024:.1f}MB exceeds limit")
        
        # Check file extension
        if file_path.suffix.lower() not in cls.ALLOWED_DOCUMENT_FORMATS:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Document format {file_path.suffix} not allowed")
        
        validation_result['metadata'] = {
            'file_type': file_path.suffix.lower(),
            'mime_type': mimetypes.guess_type(str(file_path))[0]
        }
        
        return validation_result


class LocalFileStorage:
    """Local file storage implementation."""
    
    def __init__(self, base_path: str = "data/files"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create organized directory structure
        (self.base_path / "photos" / "before").mkdir(parents=True, exist_ok=True)
        (self.base_path / "photos" / "after").mkdir(parents=True, exist_ok=True)
        (self.base_path / "photos" / "issues").mkdir(parents=True, exist_ok=True)
        (self.base_path / "documents" / "contracts").mkdir(parents=True, exist_ok=True)
        (self.base_path / "documents" / "reports").mkdir(parents=True, exist_ok=True)
        (self.base_path / "temp").mkdir(parents=True, exist_ok=True)
    
    async def upload_file(
        self, 
        file_data: bytes, 
        filename: str, 
        category: str = "general",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Upload file to local storage."""
        try:
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            safe_filename = f"{timestamp}_{file_hash}_{filename}"
            
            # Determine storage path
            if category == "photos":
                storage_path = self.base_path / "photos" / safe_filename
            elif category == "documents":
                storage_path = self.base_path / "documents" / safe_filename
            else:
                storage_path = self.base_path / safe_filename
            
            # Write file
            async with aiofiles.open(storage_path, 'wb') as f:
                await f.write(file_data)
            
            # Store metadata
            metadata_path = storage_path.with_suffix(storage_path.suffix + '.meta')
            file_metadata = {
                'original_filename': filename,
                'file_size': len(file_data),
                'upload_time': datetime.utcnow().isoformat(),
                'category': category,
                'metadata': metadata or {}
            }
            
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(file_metadata, indent=2))
            
            return {
                'status': 'success',
                'file_id': safe_filename,
                'file_path': str(storage_path),
                'file_size': len(file_data),
                'url': f"file://{storage_path}"
            }
            
        except Exception as e:
            logger.error(f"Local file upload error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file by ID."""
        try:
            # Find file in storage
            for category_dir in ['photos', 'documents', '.']:
                file_path = self.base_path / category_dir / file_id
                if file_path.exists():
                    # Get metadata
                    metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                    metadata = {}
                    if metadata_path.exists():
                        async with aiofiles.open(metadata_path, 'r') as f:
                            metadata = json.loads(await f.read())
                    
                    return {
                        'file_id': file_id,
                        'file_path': str(file_path),
                        'file_size': file_path.stat().st_size,
                        'exists': True,
                        'metadata': metadata
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file {file_id}: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file by ID."""
        try:
            # Find and delete file
            for category_dir in ['photos', 'documents', '.']:
                file_path = self.base_path / category_dir / file_id
                if file_path.exists():
                    file_path.unlink()
                    
                    # Delete metadata
                    metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                    if metadata_path.exists():
                        metadata_path.unlink()
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False


class S3FileStorage:
    """AWS S3 file storage implementation."""
    
    def __init__(self):
        self.bucket_name = settings.aws_s3_bucket
        self.s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize S3 client."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
        except NoCredentialsError:
            logger.warning("AWS credentials not found - S3 storage disabled")
            self.s3_client = None
    
    async def upload_file(
        self, 
        file_data: bytes, 
        filename: str, 
        category: str = "general",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Upload file to S3."""
        if not self.s3_client:
            return {
                'status': 'error',
                'error': 'S3 client not initialized'
            }
        
        try:
            # Generate S3 key
            timestamp = datetime.utcnow().strftime("%Y/%m/%d")
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            s3_key = f"{category}/{timestamp}/{file_hash}_{filename}"
            
            # Prepare metadata
            s3_metadata = {
                'original-filename': filename,
                'upload-time': datetime.utcnow().isoformat(),
                'category': category,
                'file-size': str(len(file_data))
            }
            
            if metadata:
                for key, value in metadata.items():
                    s3_metadata[f"custom-{key}"] = str(value)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                Metadata=s3_metadata,
                ContentType=mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            )
            
            # Generate presigned URL
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                'status': 'success',
                'file_id': s3_key,
                'file_size': len(file_data),
                'url': url,
                's3_bucket': self.bucket_name,
                's3_key': s3_key
            }
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


class FileStorageTools:
    """
    Comprehensive file storage tools for business operations.
    Handles photos, documents, and file management with validation.
    """
    
    def __init__(self):
        self.validator = FileValidator()
        self.local_storage = LocalFileStorage()
        self.s3_storage = S3FileStorage() if settings.use_s3_storage else None
        
        # Operation tracking
        self.storage_stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'photos_uploaded': 0,
            'documents_uploaded': 0,
            'total_size_uploaded': 0
        }
    
    # Core upload functions
    
    async def upload_job_photo(
        self,
        job_id: str,
        contractor_id: str,
        photo_data: Union[bytes, str],  # bytes or base64 string
        photo_type: str,  # 'before', 'after', 'issue'
        room_type: str = None,
        description: str = None
    ) -> Dict[str, Any]:
        """Upload job-related photo with business context."""
        try:
            self.storage_stats['total_uploads'] += 1
            
            # Process photo data
            if isinstance(photo_data, str):
                # Decode base64
                try:
                    photo_bytes = base64.b64decode(photo_data)
                except Exception as e:
                    return {
                        'status': 'error',
                        'error': 'invalid_base64',
                        'message': f'Invalid base64 data: {e}'
                    }
            else:
                photo_bytes = photo_data
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"job_{job_id}_{photo_type}_{timestamp}.jpg"
            
            # Validate photo
            temp_path = Path(f"temp_{filename}")
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(photo_bytes)
            
            validation = self.validator.validate_image(temp_path, len(photo_bytes))
            temp_path.unlink()  # Clean up temp file
            
            if not validation['is_valid']:
                self.storage_stats['failed_uploads'] += 1
                return {
                    'status': 'error',
                    'error': 'validation_failed',
                    'validation_errors': validation['errors']
                }
            
            # Prepare metadata
            metadata = {
                'job_id': job_id,
                'contractor_id': contractor_id,
                'photo_type': photo_type,
                'room_type': room_type,
                'description': description,
                'validation_warnings': validation['warnings'],
                'image_metadata': validation['metadata']
            }
            
            # Upload to storage
            if self.s3_storage:
                result = await self.s3_storage.upload_file(
                    photo_bytes, filename, "photos", metadata
                )
            else:
                result = await self.local_storage.upload_file(
                    photo_bytes, filename, "photos", metadata
                )
            
            if result['status'] == 'success':
                self.storage_stats['successful_uploads'] += 1
                self.storage_stats['photos_uploaded'] += 1
                self.storage_stats['total_size_uploaded'] += len(photo_bytes)
                
                logger.info(f"Photo uploaded for job {job_id}: {photo_type}")
                
                return {
                    'status': 'success',
                    'photo_id': result['file_id'],
                    'photo_url': result['url'],
                    'photo_type': photo_type,
                    'file_size': len(photo_bytes),
                    'validation_warnings': validation['warnings']
                }
            else:
                self.storage_stats['failed_uploads'] += 1
                return result
                
        except Exception as e:
            self.storage_stats['failed_uploads'] += 1
            logger.error(f"Photo upload error: {e}")
            return {
                'status': 'error',
                'error': 'upload_failed',
                'message': str(e)
            }
    
    async def upload_document(
        self,
        document_data: Union[bytes, str],
        filename: str,
        document_type: str,  # 'contract', 'report', 'invoice', 'w9'
        entity_id: str = None,  # contractor_id, job_id, etc.
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Upload business document with validation."""
        try:
            self.storage_stats['total_uploads'] += 1
            
            # Process document data
            if isinstance(document_data, str):
                try:
                    doc_bytes = base64.b64decode(document_data)
                except Exception as e:
                    return {
                        'status': 'error',
                        'error': 'invalid_base64',
                        'message': f'Invalid base64 data: {e}'
                    }
            else:
                doc_bytes = document_data
            
            # Validate document
            temp_path = Path(f"temp_{filename}")
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(doc_bytes)
            
            validation = self.validator.validate_document(temp_path, len(doc_bytes))
            temp_path.unlink()
            
            if not validation['is_valid']:
                self.storage_stats['failed_uploads'] += 1
                return {
                    'status': 'error',
                    'error': 'validation_failed',
                    'validation_errors': validation['errors']
                }
            
            # Prepare metadata
            doc_metadata = {
                'document_type': document_type,
                'entity_id': entity_id,
                'original_filename': filename,
                'validation_metadata': validation['metadata']
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            # Upload to storage
            if self.s3_storage:
                result = await self.s3_storage.upload_file(
                    doc_bytes, filename, "documents", doc_metadata
                )
            else:
                result = await self.local_storage.upload_file(
                    doc_bytes, filename, "documents", doc_metadata
                )
            
            if result['status'] == 'success':
                self.storage_stats['successful_uploads'] += 1
                self.storage_stats['documents_uploaded'] += 1
                self.storage_stats['total_size_uploaded'] += len(doc_bytes)
                
                logger.info(f"Document uploaded: {document_type} - {filename}")
                
                return {
                    'status': 'success',
                    'document_id': result['file_id'],
                    'document_url': result['url'],
                    'document_type': document_type,
                    'file_size': len(doc_bytes)
                }
            else:
                self.storage_stats['failed_uploads'] += 1
                return result
                
        except Exception as e:
            self.storage_stats['failed_uploads'] += 1
            logger.error(f"Document upload error: {e}")
            return {
                'status': 'error',
                'error': 'upload_failed',
                'message': str(e)
            }
    
    # File retrieval and management
    
    async def get_job_photos(
        self,
        job_id: str,
        photo_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get all photos for a job."""
        try:
            # For local storage, scan directory
            photos = []
            photos_dir = self.local_storage.base_path / "photos"
            
            for photo_file in photos_dir.glob(f"*job_{job_id}*"):
                if photo_file.suffix == '.meta':
                    continue
                
                # Get metadata
                metadata_path = photo_file.with_suffix(photo_file.suffix + '.meta')
                metadata = {}
                if metadata_path.exists():
                    async with aiofiles.open(metadata_path, 'r') as f:
                        metadata = json.loads(await f.read())
                
                # Filter by photo type if specified
                if photo_type and metadata.get('metadata', {}).get('photo_type') != photo_type:
                    continue
                
                photos.append({
                    'photo_id': photo_file.name,
                    'photo_type': metadata.get('metadata', {}).get('photo_type'),
                    'room_type': metadata.get('metadata', {}).get('room_type'),
                    'description': metadata.get('metadata', {}).get('description'),
                    'upload_time': metadata.get('upload_time'),
                    'file_size': metadata.get('file_size'),
                    'file_path': str(photo_file)
                })
            
            return photos
            
        except Exception as e:
            logger.error(f"Error getting job photos: {e}")
            return []
    
    async def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete file from storage."""
        try:
            # Try local storage first
            if await self.local_storage.delete_file(file_id):
                return {
                    'status': 'success',
                    'message': 'File deleted successfully'
                }
            
            # Try S3 if available
            if self.s3_storage:
                try:
                    self.s3_storage.s3_client.delete_object(
                        Bucket=self.s3_storage.bucket_name,
                        Key=file_id
                    )
                    return {
                        'status': 'success',
                        'message': 'File deleted from S3'
                    }
                except ClientError as e:
                    logger.error(f"S3 delete error: {e}")
            
            return {
                'status': 'error',
                'error': 'file_not_found',
                'message': 'File not found in any storage'
            }
            
        except Exception as e:
            logger.error(f"File deletion error: {e}")
            return {
                'status': 'error',
                'error': 'delete_failed',
                'message': str(e)
            }
    
    # Business workflow helpers
    
    async def validate_job_photos(
        self,
        job_id: str,
        required_rooms: List[str] = None
    ) -> Dict[str, Any]:
        """Validate job has required photos for compliance."""
        try:
            photos = await self.get_job_photos(job_id)
            
            if not photos:
                return {
                    'is_compliant': False,
                    'missing_requirements': ['No photos uploaded'],
                    'photo_count': 0
                }
            
            # Check for required rooms
            required_rooms = required_rooms or ['kitchen', 'bathroom', 'entry']
            covered_rooms = set()
            
            for photo in photos:
                room_type = photo.get('room_type', '').lower()
                if room_type:
                    covered_rooms.add(room_type)
            
            missing_rooms = []
            for required_room in required_rooms:
                if not any(required_room.lower() in room for room in covered_rooms):
                    missing_rooms.append(required_room)
            
            # Check for before/after coverage
            photo_types = {photo.get('photo_type') for photo in photos}
            missing_types = []
            
            if 'before' not in photo_types:
                missing_types.append('before photos')
            if 'after' not in photo_types:
                missing_types.append('after photos')
            
            missing_requirements = missing_rooms + missing_types
            
            return {
                'is_compliant': len(missing_requirements) == 0,
                'missing_requirements': missing_requirements,
                'photo_count': len(photos),
                'covered_rooms': list(covered_rooms),
                'photo_types': list(photo_types)
            }
            
        except Exception as e:
            logger.error(f"Photo validation error: {e}")
            return {
                'is_compliant': False,
                'error': str(e),
                'photo_count': 0
            }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get file storage statistics."""
        stats = self.storage_stats.copy()
        
        if stats['total_uploads'] > 0:
            stats['success_rate'] = (stats['successful_uploads'] / stats['total_uploads']) * 100
        else:
            stats['success_rate'] = 0
        
        stats['total_size_mb'] = stats['total_size_uploaded'] / 1024 / 1024
        
        return stats


# Agent tool wrappers

class FileAgentTools:
    """
    Simplified file tools for agent use.
    Provides high-level business functions.
    """
    
    def __init__(self):
        self.storage = FileStorageTools()
    
    async def upload_completion_photos(
        self,
        job_id: str,
        contractor_id: str,
        photos: List[Dict[str, Any]]  # [{'data': bytes, 'room': str, 'description': str}]
    ) -> Dict[str, Any]:
        """Agent tool: Upload job completion photos."""
        results = []
        
        for photo in photos:
            result = await self.storage.upload_job_photo(
                job_id=job_id,
                contractor_id=contractor_id,
                photo_data=photo['data'],
                photo_type='after',
                room_type=photo.get('room'),
                description=photo.get('description')
            )
            results.append(result)
        
        successful_uploads = [r for r in results if r['status'] == 'success']
        
        return {
            'total_photos': len(photos),
            'successful_uploads': len(successful_uploads),
            'failed_uploads': len(photos) - len(successful_uploads),
            'results': results
        }
    
    async def validate_job_compliance(
        self,
        job_id: str,
        service_type: str = "recurring"
    ) -> Dict[str, Any]:
        """Agent tool: Validate job photo compliance."""
        
        # Define required rooms by service type
        required_rooms_map = {
            'recurring': ['kitchen', 'bathroom', 'entry'],
            'deep_cleaning': ['kitchen', 'bathroom', 'entry', 'living_room'],
            'move_out_in': ['kitchen', 'bathroom', 'entry', 'all_rooms']
        }
        
        required_rooms = required_rooms_map.get(service_type, ['kitchen', 'bathroom'])
        
        return await self.storage.validate_job_photos(job_id, required_rooms)
    
    async def get_storage_summary(self) -> Dict[str, Any]:
        """Agent tool: Get storage system summary."""
        return self.storage.get_storage_stats()