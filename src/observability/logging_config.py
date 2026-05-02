# Structured Logging Configuration
import logging
import logging.config
from pythonjsonlogger import jsonlogger
import sys
from typing import Dict, Any

class StructuredLogger:
    @staticmethod
    def setup_logging(log_level: str = "INFO", json_format: bool = True):
        """Setup structured logging"""
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, log_level.upper()))

        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create formatter
        if json_format:
            formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger with the specified name"""
        return logging.getLogger(name)

# Global logger instance
logger = StructuredLogger.get_logger(__name__)

def log_request(request_id: str, method: str, endpoint: str, **kwargs):
    """Log API request"""
    logger.info("API Request", extra={
        'request_id': request_id,
        'method': method,
        'endpoint': endpoint,
        **kwargs
    })

def log_embedding_generation(doc_count: int, batch_size: int, duration: float):
    """Log embedding generation metrics"""
    logger.info("Embedding Generation Completed", extra={
        'doc_count': doc_count,
        'batch_size': batch_size,
        'duration_seconds': duration,
        'throughput': doc_count / duration if duration > 0 else 0
    })

def log_search_query(query: str, results_count: int, duration: float):
    """Log search query metrics"""
    logger.info("Search Query Executed", extra={
        'query_length': len(query),
        'results_count': results_count,
        'duration_seconds': duration
    })
