"""
Tasks module - Sistema de tareas en segundo plano con RQ
"""

from .ml_tasks import process_report_ml_detection, test_task

__all__ = [
    "process_report_ml_detection",
    "test_task",
]
