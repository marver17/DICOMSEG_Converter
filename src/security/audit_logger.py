#!/usr/bin/env python3
"""
Audit Logger - Centralized structured logging for EUCAIM compliance
Implements security and audit logging requirements
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import os
from pathlib import Path


class AuditLogger:
    """
    Centralized structured audit logging for security and compliance.
    
    Features:
    - JSON-structured logs for easy parsing
    - Separate audit trail from application logs
    - Security event tracking
    - Compliance-ready format
    """
    
    def __init__(self, log_dir: str = "/logs", verbose: bool = False):
        """
        Initialize the audit logger.
        
        Args:
            log_dir: Directory for log files
            verbose: If True, also log to console
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("dicomconverter.audit")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []  # Clear any existing handlers
        
        # JSON file handler for audit logs
        audit_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        file_handler = logging.FileHandler(audit_file)
        file_handler.setFormatter(self.JSONFormatter())
        file_handler.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
        # Console handler (optional, for debugging)
        if verbose:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    class JSONFormatter(logging.Formatter):
        """Format log records as JSON."""
        
        def format(self, record):
            log_obj = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'message': record.getMessage(),
                'logger': record.name,
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
            }
            
            # Add custom audit data if present
            if hasattr(record, 'audit_data'):
                log_obj['audit'] = record.audit_data
            
            return json.dumps(log_obj)
    
    def log_conversion_start(
        self, 
        conversion_type: str,
        input_path: str,
        output_path: str,
        user_id: Optional[str] = None,
        job_id: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ):
        """
        Log the start of a conversion operation.
        
        Args:
            conversion_type: Type of conversion (e.g., 'rtstruct2seg', 'dicom2nifti')
            input_path: Input file/directory path
            output_path: Output file/directory path
            user_id: User identifier (if available)
            job_id: Unique job identifier
            additional_params: Additional parameters for the conversion
        """
        self.logger.info(
            f"Conversion started: {conversion_type}",
            extra={'audit_data': {
                'event_type': 'conversion_start',
                'conversion_type': conversion_type,
                'input': self._sanitize_path(input_path),
                'output': self._sanitize_path(output_path),
                'user_id': user_id or 'unknown',
                'job_id': job_id or 'N/A',
                'params': additional_params or {}
            }}
        )
    
    def log_conversion_end(
        self,
        conversion_type: str,
        status: str,  # 'success' or 'failure'
        duration_seconds: float,
        job_id: Optional[str] = None,
        output_size_mb: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Log the completion of a conversion operation.
        
        Args:
            conversion_type: Type of conversion
            status: 'success' or 'failure'
            duration_seconds: Execution time
            job_id: Unique job identifier
            output_size_mb: Size of output file(s) in MB
            error: Error message if status is 'failure'
        """
        level = logging.INFO if status == 'success' else logging.ERROR
        
        self.logger.log(
            level,
            f"Conversion ended: {conversion_type} - {status}",
            extra={'audit_data': {
                'event_type': 'conversion_end',
                'conversion_type': conversion_type,
                'status': status,
                'duration_seconds': round(duration_seconds, 2),
                'job_id': job_id or 'N/A',
                'output_size_mb': round(output_size_mb, 2) if output_size_mb else None,
                'error': self._sanitize_error(error) if error else None
            }}
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,  # 'low', 'medium', 'high', 'critical'
        description: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """
        Log security-relevant events.
        
        Args:
            event_type: Type of security event (e.g., 'unauthorized_access', 'validation_failure')
            severity: Severity level
            description: Human-readable description
            details: Additional details about the event
            user_id: User identifier if applicable
        """
        level_map = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL
        }
        level = level_map.get(severity, logging.WARNING)
        
        self.logger.log(
            level,
            f"SECURITY: {event_type} - {description}",
            extra={'audit_data': {
                'event_type': 'security_event',
                'security_event_type': event_type,
                'severity': severity,
                'description': description,
                'details': details or {},
                'user_id': user_id or 'unknown'
            }}
        )
    
    def log_resource_usage(
        self,
        resource_type: str,  # 'memory', 'cpu', 'disk', 'duration'
        usage: float,
        limit: float,
        unit: str,
        job_id: Optional[str] = None
    ):
        """
        Log resource usage for monitoring.
        
        Args:
            resource_type: Type of resource
            usage: Current usage value
            limit: Limit/threshold value
            unit: Unit of measurement (e.g., 'MB', 'percent', 'seconds')
            job_id: Job identifier
        """
        percent_used = (usage / limit * 100) if limit > 0 else 0
        is_warning = percent_used > 80  # Warning if over 80% of limit
        
        level = logging.WARNING if is_warning else logging.INFO
        
        self.logger.log(
            level,
            f"Resource usage: {resource_type} at {percent_used:.1f}%",
            extra={'audit_data': {
                'event_type': 'resource_usage',
                'resource_type': resource_type,
                'usage': round(usage, 2),
                'limit': round(limit, 2),
                'unit': unit,
                'percent_used': round(percent_used, 1),
                'is_warning': is_warning,
                'job_id': job_id or 'N/A'
            }}
        )
    
    def log_system_startup(self, version_info: Dict[str, str]):
        """
        Log system startup with version information.
        
        Args:
            version_info: Dictionary with version, git_commit, build_date, etc.
        """
        self.logger.info(
            "System startup",
            extra={'audit_data': {
                'event_type': 'system_startup',
                'version': version_info
            }}
        )
    
    def log_validation_result(
        self,
        validation_type: str,
        passed: bool,
        details: Dict[str, Any],
        job_id: Optional[str] = None
    ):
        """
        Log validation results (geometric, DICOM, etc.).
        
        Args:
            validation_type: Type of validation
            passed: Whether validation passed
            details: Validation details
            job_id: Job identifier
        """
        level = logging.INFO if passed else logging.WARNING
        
        self.logger.log(
            level,
            f"Validation {validation_type}: {'PASS' if passed else 'FAIL'}",
            extra={'audit_data': {
                'event_type': 'validation_result',
                'validation_type': validation_type,
                'passed': passed,
                'details': details,
                'job_id': job_id or 'N/A'
            }}
        )
    
    def _sanitize_path(self, path: str) -> str:
        """Remove sensitive information from paths for logging."""
        if not path:
            return ''
        
        # Replace home directory
        sanitized = path.replace(str(Path.home()), '~')
        
        # Show only last few components
        parts = Path(sanitized).parts
        if len(parts) > 4:
            sanitized = '.../' + '/'.join(parts[-3:])
        
        return sanitized
    
    def _sanitize_error(self, error: str) -> str:
        """Sanitize error messages to remove sensitive info."""
        if not error:
            return ''
        
        # Remove absolute paths
        import re
        sanitized = re.sub(r'/[\w/]+/', '/...//', error)
        
        # Limit length
        max_len = 500
        if len(sanitized) > max_len:
            sanitized = sanitized[:max_len] + '... (truncated)'
        
        return sanitized


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(log_dir: str = "/logs", verbose: bool = False) -> AuditLogger:
    """
    Get the singleton audit logger instance.
    
    Args:
        log_dir: Directory for log files (only used on first call)
        verbose: Enable verbose logging (only used on first call)
        
    Returns:
        AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_dir=log_dir, verbose=verbose)
    return _audit_logger


# Example usage
if __name__ == '__main__':
    import time
    
    print("AuditLogger - Test Suite\n")
    
    # Create logger (in /tmp for testing)
    logger = get_audit_logger(log_dir='/tmp/dicomconverter_test_logs', verbose=True)
    
    # Test system startup
    logger.log_system_startup({
        'version': '1.4.0',
        'git_commit': 'abc123',
        'build_date': '2025-12-10'
    })
    
    # Test conversion lifecycle
    job_id = f"test_job_{int(time.time())}"
    
    logger.log_conversion_start(
        conversion_type='rtstruct2seg',
        input_path='/data/test/input.dcm',
        output_path='/data/test/output.dcm',
        user_id='test_user',
        job_id=job_id,
        additional_params={'algorithm': 'standard'}
    )
    
    # Simulate work
    time.sleep(0.5)
    
    logger.log_conversion_end(
        conversion_type='rtstruct2seg',
        status='success',
        duration_seconds=0.5,
        job_id=job_id,
        output_size_mb=15.3
    )
    
    # Test security event
    logger.log_security_event(
        event_type='path_validation_failure',
        severity='medium',
        description='Attempted access to unauthorized path',
        details={'attempted_path': '/etc/passwd'},
        user_id='malicious_user'
    )
    
    # Test resource usage
    logger.log_resource_usage(
        resource_type='memory',
        usage=6500,
        limit=8000,
        unit='MB',
        job_id=job_id
    )
    
    # Test validation
    logger.log_validation_result(
        validation_type='geometric',
        passed=True,
        details={'dice_score': 0.98, 'checks_passed': 4},
        job_id=job_id
    )
    
    print(f"\nTest logs written to: /tmp/dicomconverter_test_logs/")
    print("Check the audit_*.jsonl file for JSON-formatted logs")
