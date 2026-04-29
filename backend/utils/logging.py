# backend/utils/logging.py
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json
from decimal import Decimal

class SetEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles sets and other non-serializable types"""
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class AuditLogger:
    """Audit logger for POPIA compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if no handlers exist
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
            self.logger.addHandler(console_handler)
    
    def log(self, event: str, user_id: Optional[int] = None, 
            action: Optional[str] = None, details: Optional[Dict] = None,
            sensitive: bool = False):
        """
        Log an audit event
        
        Args:
            event: Description of the event (required)
            user_id: User who performed the action
            action: Action type (CREATE, READ, UPDATE, DELETE, VERIFY, etc.)
            details: Additional event details
            sensitive: Whether this log contains sensitive data
        """
        log_entry = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if user_id:
            log_entry["user_id"] = user_id
        if action:
            log_entry["action"] = action
        if details:
            # Clean the details to ensure JSON serializable
            cleaned_details = self._clean_for_json(details)
            if sensitive:
                cleaned_details = self._sanitize_sensitive_data(cleaned_details)
            log_entry["details"] = cleaned_details
        
        # Use custom encoder to handle sets
        self.logger.info(json.dumps(log_entry, cls=SetEncoder))
    
    def _clean_for_json(self, obj):
        """Recursively convert non-JSON-serializable objects"""
        if isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._clean_for_json(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return self._clean_for_json(obj.__dict__)
        else:
            return obj
    
    def _sanitize_sensitive_data(self, data: Dict) -> Dict:
        """Remove sensitive information from logs"""
        sensitive_fields = ['password', 'token', 'biometric_hash', 'face_image', 
                           'ssn', 'id_number', 'credit_card']
        sanitized = {}
        for key, value in data.items():
            if key.lower() in sensitive_fields:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_sensitive_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_sensitive_data(item) if isinstance(item, dict) else item 
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

# Create a global instance
audit_logger = AuditLogger()

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)