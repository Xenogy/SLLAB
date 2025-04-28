"""
Error reporting for the AccountDB application.

This module provides functions for reporting errors to various channels.
"""

import os
import time
import json
import logging
import traceback
from typing import Optional, Dict, List, Any, Union, Callable
from fastapi import Request

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Error tracking
error_counts = {}
error_last_reported = {}
error_rate_limits = {}

def log_error(
    exception: Exception,
    request_or_extra: Optional[Union[Request, Dict[str, Any]]] = None,
    level: int = logging.ERROR,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error.

    Args:
        exception: The exception to log
        request_or_extra: The request that caused the exception or extra information
        level: The logging level to use
        extra: Additional information to log
    """
    # Get exception details
    exc_type = type(exception).__name__
    exc_message = str(exception)
    exc_traceback = traceback.format_exc()

    # Determine if request_or_extra is a Request or extra data
    request = None
    extra_data = extra or {}

    if isinstance(request_or_extra, Request):
        request = request_or_extra
    elif isinstance(request_or_extra, dict):
        extra_data = request_or_extra

    # Get request details
    request_details = {}
    if request:
        request_details = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
            "headers": dict(request.headers),
            "request_id": getattr(request.state, "request_id", None)
        }

    # Combine all details
    log_data = {
        "exception": {
            "type": exc_type,
            "message": exc_message,
            "traceback": exc_traceback
        },
        "request": request_details,
        **(extra_data)
    }

    # Log the error
    log_message = f"{exc_type}: {exc_message}"
    if request:
        log_message = f"{request.method} {request.url.path} - {log_message}"

    logger.log(level, log_message, extra={"error_data": log_data})

def report_error(
    exception: Exception,
    request_or_extra: Optional[Union[Request, Dict[str, Any]]] = None,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Report an error to external services.

    Args:
        exception: The exception to report
        request_or_extra: The request that caused the exception or extra information
        extra: Additional information to report
    """
    # Check if error reporting is enabled
    if not getattr(Config, "ERROR_REPORTING_ENABLED", False):
        return

    # Get exception details
    exc_type = type(exception).__name__
    exc_message = str(exception)

    # Check rate limiting
    if not should_report_error(exc_type):
        logger.debug(f"Rate limited error report for {exc_type}: {exc_message}")
        return

    # Determine if request_or_extra is a Request or extra data
    request = None
    extra_data = extra or {}

    if isinstance(request_or_extra, Request):
        request = request_or_extra
    elif isinstance(request_or_extra, dict):
        extra_data = request_or_extra

    # Get request details
    request_details = {}
    if request:
        request_details = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
            "headers": dict(request.headers),
            "request_id": getattr(request.state, "request_id", None)
        }

    # Combine all details
    report_data = {
        "exception": {
            "type": exc_type,
            "message": exc_message,
            "traceback": traceback.format_exc()
        },
        "request": request_details,
        "environment": getattr(Config, "ENVIRONMENT", "development"),
        "timestamp": time.time(),
        **(extra_data)
    }

    # Report to configured services
    report_to_services(report_data)

    # Update error tracking
    track_error(exc_type)

def report_to_services(report_data: Dict[str, Any]) -> None:
    """
    Report an error to configured services.

    Args:
        report_data: The error data to report
    """
    # Report to Sentry
    if getattr(Config, "SENTRY_DSN", None):
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(
                error=report_data["exception"].get("traceback"),
                extra=report_data
            )
        except Exception as e:
            logger.error(f"Error reporting to Sentry: {e}")

    # Report to Slack
    if getattr(Config, "SLACK_WEBHOOK_URL", None):
        try:
            import requests

            # Format the message
            message = {
                "text": f"Error: {report_data['exception']['type']}: {report_data['exception']['message']}",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {
                                "title": "Environment",
                                "value": report_data["environment"],
                                "short": True
                            },
                            {
                                "title": "Request",
                                "value": f"{report_data['request'].get('method', 'N/A')} {report_data['request'].get('url', 'N/A')}",
                                "short": True
                            }
                        ]
                    }
                ]
            }

            # Send the message
            requests.post(
                Config.SLACK_WEBHOOK_URL,
                json=message,
                timeout=5
            )
        except Exception as e:
            logger.error(f"Error reporting to Slack: {e}")

    # Report to email
    if getattr(Config, "ERROR_EMAIL_TO", None):
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Format the message
            subject = f"Error: {report_data['exception']['type']}: {report_data['exception']['message']}"
            body = f"""
            <h1>Error Report</h1>
            <p><strong>Type:</strong> {report_data['exception']['type']}</p>
            <p><strong>Message:</strong> {report_data['exception']['message']}</p>
            <p><strong>Environment:</strong> {report_data['environment']}</p>
            <p><strong>Request:</strong> {report_data['request'].get('method', 'N/A')} {report_data['request'].get('url', 'N/A')}</p>
            <p><strong>Timestamp:</strong> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report_data['timestamp']))}</p>
            <h2>Traceback</h2>
            <pre>{report_data['exception'].get('traceback', 'N/A')}</pre>
            """

            # Create the email
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = getattr(Config, "ERROR_EMAIL_FROM", "errors@accountdb.app")
            msg["To"] = Config.ERROR_EMAIL_TO

            # Attach the body
            msg.attach(MIMEText(body, "html"))

            # Send the email
            smtp = smtplib.SMTP(
                getattr(Config, "SMTP_HOST", "localhost"),
                getattr(Config, "SMTP_PORT", 25)
            )
            if getattr(Config, "SMTP_USE_TLS", False):
                smtp.starttls()
            if getattr(Config, "SMTP_USERNAME", None) and getattr(Config, "SMTP_PASSWORD", None):
                smtp.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            smtp.send_message(msg)
            smtp.quit()
        except Exception as e:
            logger.error(f"Error reporting to email: {e}")

def track_error(error_type: str) -> None:
    """
    Track an error for rate limiting.

    Args:
        error_type: The type of error to track
    """
    # Initialize tracking for this error type
    if error_type not in error_counts:
        error_counts[error_type] = 0
        error_last_reported[error_type] = 0

    # Update error count
    error_counts[error_type] += 1

    # Update last reported time
    error_last_reported[error_type] = time.time()

def should_report_error(error_type: str) -> bool:
    """
    Check if an error should be reported based on rate limiting.

    Args:
        error_type: The type of error to check

    Returns:
        bool: True if the error should be reported, False otherwise
    """
    # Get rate limit for this error type
    rate_limit = error_rate_limits.get(
        error_type,
        getattr(Config, "ERROR_RATE_LIMIT", 60)  # Default: 1 per minute
    )

    # If no rate limit, always report
    if rate_limit <= 0:
        return True

    # If error has never been reported, report it
    if error_type not in error_last_reported:
        return True

    # Check if enough time has passed since last report
    time_since_last_report = time.time() - error_last_reported[error_type]
    return time_since_last_report >= rate_limit

def get_error_summary() -> Dict[str, Any]:
    """
    Get a summary of tracked errors.

    Returns:
        Dict[str, Any]: The error summary
    """
    return {
        "counts": error_counts,
        "last_reported": {
            error_type: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            for error_type, timestamp in error_last_reported.items()
        },
        "rate_limits": error_rate_limits
    }

def track_error_rate(error_type: str, rate_limit: int) -> None:
    """
    Set the rate limit for an error type.

    Args:
        error_type: The type of error to set the rate limit for
        rate_limit: The rate limit in seconds (0 for no limit)
    """
    error_rate_limits[error_type] = rate_limit

def notify_error(
    message: str,
    level: str = "error",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Send a notification about an error.

    Args:
        message: The error message
        level: The error level (error, warning, info)
        details: Additional details about the error
    """
    # Check if notifications are enabled
    if not getattr(Config, "NOTIFICATIONS_ENABLED", False):
        return

    # Map level to color
    color_map = {
        "error": "danger",
        "warning": "warning",
        "info": "good"
    }
    color = color_map.get(level, "danger")

    # Format the notification
    notification = {
        "text": f"{level.upper()}: {message}",
        "attachments": [
            {
                "color": color,
                "fields": [
                    {
                        "title": "Environment",
                        "value": getattr(Config, "ENVIRONMENT", "development"),
                        "short": True
                    },
                    {
                        "title": "Timestamp",
                        "value": time.strftime('%Y-%m-%d %H:%M:%S'),
                        "short": True
                    }
                ]
            }
        ]
    }

    # Add details if provided
    if details:
        for key, value in details.items():
            notification["attachments"][0]["fields"].append({
                "title": key,
                "value": str(value),
                "short": len(str(value)) < 20
            })

    # Send to Slack
    if getattr(Config, "SLACK_WEBHOOK_URL", None):
        try:
            import requests
            requests.post(
                Config.SLACK_WEBHOOK_URL,
                json=notification,
                timeout=5
            )
        except Exception as e:
            logger.error(f"Error sending notification to Slack: {e}")
