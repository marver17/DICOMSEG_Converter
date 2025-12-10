"""
EUCAIM Security Module
======================

This module provides security utilities for the DicomConverter application:
- PathValidator: Input validation and path sanitization
- AuditLogger: Structured logging for compliance

Usage:
    from security.path_validator import PathValidator
    from security.audit_logger import AuditLogger
"""

__version__ = "1.0.0"
__all__ = ["PathValidator", "AuditLogger"]
