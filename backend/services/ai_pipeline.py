# services/ai_pipeline.py
import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional, List
import torch
import asyncio
from datetime import datetime
from collections import deque
import hashlib
import json

from core.config import settings
from utils.logging import get_logger

logger = get_logger(__name__)

class AIPipelineService:
    """
    AI Pipeline for facial recognition exam attendance
    Pipeline: YOLOv8-Face -> MediaPipe -> ArcFace -> DINOv2 PAD
    """
    
    def __init__(self):
        self.models_loaded = False
        self.yolo_model = None
        self.mediapipe_model = None
        self.arcface_model = None
        self.dinov2_model = None
        
        # Performance tracking
        self.inference_times = deque(maxlen=1000)
        self.queue_size = 0
        self.processing_lock = asyncio.Lock()
        
        # Device configuration
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"AI Pipeline using device: {self.device}")
        
        # Initialize models
        self._load_models()
    
    def _load_models(self):
        """Load all AI models into memory"""
        try:
            # Load YOLOv8-Face for face detection
            from ultralytics import YOLO
            self.yolo_model = YOLO(f"{settings.AI_MODELS_PATH}/yolov8n-face.pt")
            self.yolo_model.to(self.device)
            logger.info("YOLOv8-Face model loaded")
            
            # Load MediaPipe for face alignment
            import mediapipe as mp
            self.mediapipe_model = mp.solutions.face_mesh
            self.mediapipe_model = self.mediapipe_model.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            logger.info("MediaPipe landmark model loaded")
            
            # Load ArcFace for face recognition
            import insightface
            self.arcface_model = insightface.app.FaceAnalysis(
                name='buffalo_l',
                root=settings.AI_MODELS_PATH,
                allowed_modules=['detection', 'recognition']
            )
            self.arcface_model.prepare(ctx_id=0 if torch.cuda.is_available() else -1)
            logger.info("ArcFace recognition model loaded")
            
            # Load DINOv2 for liveness detection
            from transformers import AutoImageProcessor, AutoModelForImageClassification
            self.dinov2_processor = AutoImageProcessor.from_pretrained(
                f"{settings.AI_MODELS_PATH}/dinov2-small"
            )
            self.dinov2_model = AutoModelForImageClassification.from_pretrained(
                f"{settings.AI_MODELS_PATH}/dinov2-small"
            )
            self.dinov2_model.to(self.device)
            self.dinov2_model.eval()
            logger.info("DINOv2 PAD model loaded")
            
            self.models_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load AI models: {str(e)}")
            self.models_loaded = False
            raise
    
    async def process_face(
        self, 
        image_bytes: bytes,
        student_biometric_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process face through the entire AI pipeline
        
        Args:
            image_bytes: Raw image bytes from camera
            student_biometric_hash: Stored hash for comparison
        
        Returns:
            Dict with detection, recognition, and liveness results
        """
        if not self.models_loaded:
            raise RuntimeError("AI models not loaded")
        
        start_time = datetime.now()
        
        async with self.processing_lock:
            self.queue_size += 1
            try:
                # Convert bytes to image
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    return {
                        "success": False,
                        "error": "Invalid image format",
                        "face_detected": False
                    }
                
                # Step 1: Face Detection (YOLOv8)
                detection_result = await self._detect_face(image)
                if not detection_result["face_detected"]:
                    return {
                        "success": False,
                        "error": "No face detected",
                        "face_detected": False,
                        "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                    }
                
                # Step 2: Face Alignment (MediaPipe)
                aligned_face = await self._align_face(image, detection_result["bbox"])
                if aligned_face is None:
                    return {
                        "success": False,
                        "error": "Face alignment failed",
                        "face_detected": True,
                        "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                    }
                
                # Step 3: Feature Extraction (ArcFace)
                face_embedding = await self._extract_features(aligned_face)
                
                # Step 4: Liveness Detection (DINOv2)
                liveness_result = await self._check_liveness(aligned_face)
                
                # Step 5: Face Matching (if biometric hash provided)
                match_result = None
                if student_biometric_hash:
                    match_result = await self._match_face(
                        face_embedding, 
                        student_biometric_hash
                    )
                
                # Calculate processing time
                processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                self.inference_times.append(processing_time_ms)
                
                return {
                    "success": True,
                    "face_detected": True,
                    "liveness_score": liveness_result["score"],
                    "is_live": liveness_result["is_live"],
                    "match_score": match_result["score"] if match_result else None,
                    "is_match": match_result["is_match"] if match_result else None,
                    "confidence": match_result["confidence"] if match_result else None,
                    "face_embedding": face_embedding.tolist() if face_embedding is not None else None,
                    "processing_time_ms": processing_time_ms,
                    "bbox": detection_result["bbox"],
                    "landmarks": detection_result["landmarks"]
                }
                
            except Exception as e:
                logger.error(f"Face processing error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "face_detected": False,
                    "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
            finally:
                self.queue_size -= 1
    
    async def _detect_face(self, image: np.ndarray) -> Dict[str, Any]:
        """YOLOv8 face detection"""
        try:
            # Run inference
            results = self.yolo_model(image, verbose=False)
            
            if len(results[0].boxes) == 0:
                return {"face_detected": False, "bbox": None, "landmarks": None}
            
            # Get first face
            box = results[0].boxes[0]
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            confidence = float(box.conf[0])
            
            # Extract landmarks if available
            landmarks = None
            if hasattr(results[0], 'keypoints') and len(results[0].keypoints) > 0:
                landmarks = results[0].keypoints[0].xy[0].tolist()
            
            return {
                "face_detected": True,
                "bbox": [x1, y1, x2, y2],
                "confidence": confidence,
                "landmarks": landmarks
            }
        except Exception as e:
            logger.error(f"Face detection error: {str(e)}")
            return {"face_detected": False, "bbox": None, "landmarks": None}
    
    async def _align_face(self, image: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """MediaPipe face alignment"""
        try:
            x1, y1, x2, y2 = bbox
            face_roi = image[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                return None
            
            # Convert to RGB for MediaPipe
            rgb_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
            
            # Detect landmarks
            results = self.mediapipe_model.process(rgb_face)
            
            if not results.multi_face_landmarks:
                return face_roi  # Return unaligned if landmarks not found
            
            # Simple alignment (can be enhanced with affine transform)
            aligned = cv2.resize(face_roi, (112, 112))
            return aligned
            
        except Exception as e:
            logger.error(f"Face alignment error: {str(e)}")
            return None
    
    async def _extract_features(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """ArcFace feature extraction"""
        try:
            # Prepare face for ArcFace
            faces = self.arcface_model.get(face_image)
            
            if len(faces) == 0:
                return None
            
            # Extract embedding
            embedding = faces[0].embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Feature extraction error: {str(e)}")
            return None
    
    async def _check_liveness(self, face_image: np.ndarray) -> Dict[str, Any]:
        """DINOv2 liveness detection (anti-spoofing)"""
        try:
            # Preprocess image
            from PIL import Image
            
            # Convert to PIL Image
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(face_rgb)
            
            # Process with DINOv2
            inputs = self.dinov2_processor(images=pil_image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.dinov2_model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=1)
            
            # Get liveness probability (assuming binary classification)
            liveness_score = float(probabilities[0][1])  # 1 = live, 0 = spoof
            is_live = liveness_score > settings.LIVENESS_THRESHOLD
            
            return {
                "score": liveness_score,
                "is_live": is_live,
                "threshold": settings.LIVENESS_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Liveness detection error: {str(e)}")
            return {"score": 0.5, "is_live": False, "error": str(e)}
    
    async def _match_face(
        self, 
        embedding: np.ndarray, 
        stored_hash: str
    ) -> Dict[str, Any]:
        """Match extracted features with stored biometric hash"""
        try:
            # In production, you would compare against stored embeddings
            # For now, we'll simulate matching
            
            # Calculate similarity score (cosine distance)
            # This is simplified - in reality, you'd compare against stored embedding
            
            # Simulate match score based on hash comparison
            # In production: compare embedding with stored embedding from database
            import random
            match_score = random.uniform(0.5, 0.95)  # Simulated score
            
            is_match = match_score > settings.FACE_MATCH_THRESHOLD
            
            return {
                "score": match_score,
                "is_match": is_match,
                "confidence": match_score if is_match else 1 - match_score,
                "threshold": settings.FACE_MATCH_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Face matching error: {str(e)}")
            return {"score": 0.0, "is_match": False, "error": str(e)}
    
    async def get_avg_inference_time(self) -> float:
        """Get average inference time in milliseconds"""
        if len(self.inference_times) == 0:
            return 0.0
        return sum(self.inference_times) / len(self.inference_times)
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue_size
    
    async def check_yolov8(self) -> bool:
        """Check if YOLOv8 model is loaded"""
        return self.yolo_model is not None
    
    async def check_mediapipe(self) -> bool:
        """Check if MediaPipe model is loaded"""
        return self.mediapipe_model is not None
    
    async def check_arcface(self) -> bool:
        """Check if ArcFace model is loaded"""
        return self.arcface_model is not None
    
    async def check_dinov2(self) -> bool:
        """Check if DINOv2 model is loaded"""
        return self.dinov2_model is not None
    
    async def generate_biometric_hash(self, face_embedding: np.ndarray) -> str:
        """Generate a secure hash from face embedding for storage (POPIA compliant)"""
        # Convert embedding to bytes
        embedding_bytes = face_embedding.tobytes()
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(embedding_bytes)
        hash_obj.update(b"salt")  # Add pepper/salt
        
        return hash_obj.hexdigest()
    
    async def clear_cache(self):
        """Clear model cache to free memory"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("AI model cache cleared")
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for all models"""
        return {
            "models_loaded": self.models_loaded,
            "device": str(self.device),
            "gpu_available": torch.cuda.is_available(),
            "gpu_memory_mb": torch.cuda.memory_allocated() / 1024**2 if torch.cuda.is_available() else 0,
            "queue_size": self.queue_size,
            "avg_inference_time_ms": await self.get_avg_inference_time(),
            "samples_processed": len(self.inference_times),
            "thresholds": {
                "face_match": settings.FACE_MATCH_THRESHOLD,
                "liveness": settings.LIVENESS_THRESHOLD
            }
        }