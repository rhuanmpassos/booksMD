"""Módulo de tarefas assíncronas."""

from .celery_app import celery_app
from .book_tasks import process_book_task

__all__ = ["celery_app", "process_book_task"]

