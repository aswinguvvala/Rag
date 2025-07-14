# utils/logging_config.py
import logging
import structlog
from structlog import processors
from pathlib import Path
import json
from datetime import datetime

def setup_logging(log_level: str = "INFO"):
    """Configure structured logging for the application"""
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            processors.TimeStamper(fmt="iso"),
            processors.StackInfoRenderer(),
            processors.format_exc_info,
            processors.UnicodeDecoder(),
            processors.CallsiteParameterAdder(
                parameters=[
                    processors.CallsiteParameter.FILENAME,
                    processors.CallsiteParameter.LINENO,
                    processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/mseis_{datetime.now().strftime('%Y%m%d')}.log")
        ]
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name) 