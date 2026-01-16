"""
Observability module for Agent Evaluation, Safety & Observability.

This module provides logging, querying, baseline management, and validation
services for tracking agent decisions and tool invocations.

Feature: 004-agent-observability
"""

from .baseline_service import BaselineService
from .categories import ErrorCode, OutcomeCategory, assign_outcome_category
from .database import cleanup_old_logs, get_log_db, init_log_db
from .logging_service import LoggingService
from .models import (
    BaselineSnapshot,
    DecisionLog,
    DecisionTrace,
    DriftReport,
    MetricsSummary,
    QueryResult,
    TestCase,
    ToolInvocationLog,
    ValidationReport,
)
from .query_service import LogQueryService
from .validation_service import ValidationService

__all__ = [
    # Database
    "get_log_db",
    "init_log_db",
    "cleanup_old_logs",
    # Models
    "DecisionLog",
    "ToolInvocationLog",
    "BaselineSnapshot",
    "ValidationReport",
    "DecisionTrace",
    "QueryResult",
    "MetricsSummary",
    "DriftReport",
    "TestCase",
    # Categories
    "OutcomeCategory",
    "ErrorCode",
    "assign_outcome_category",
    # Services
    "LoggingService",
    "LogQueryService",
    "BaselineService",
    "ValidationService",
]
