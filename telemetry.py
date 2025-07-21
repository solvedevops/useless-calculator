"""
Shared telemetry module for all microservices.
Supports multiple logging destinations based on TELEMETRY_MODE environment variable.
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from logging.handlers import RotatingFileHandler
import traceback

# For cloud logging support
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.core.exceptions import AzureError
    
    # OpenTelemetry instrumentation imports
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    
    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False


class CloudWatchHandler(logging.Handler):
    """Custom handler for AWS CloudWatch Logs with structured paths."""
    
    def __init__(self, service_name: str, data_type: str = "logs", region: str = None):
        super().__init__()
        if not HAS_BOTO3:
            raise ImportError("boto3 is required for CloudWatch logging. Install with: pip install boto3")
        
        # Get environment variables for structured paths
        env_name = os.environ.get('ENV_NAME', 'development')
        app_name = os.environ.get('APP_NAME', 'useless-calculator')
        
        # AWS Best Practice: Single log group per service, separate log streams for data types
        self.log_group = f"/aws/microservice/{env_name}/{service_name}"       
        # Create log stream with data type, hostname and date
        import socket
        hostname = socket.gethostname()
        date_str = datetime.now().strftime('%Y/%m/%d')
        self.log_stream = f"{data_type}/{hostname}/{date_str}"
        
        self.region = region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        self.service_name = service_name
        self.data_type = data_type
        
        # Initialize CloudWatch client
        self.client = boto3.client('logs', region_name=self.region)
        self.sequence_token = None
        
        # Create log group and stream if they don't exist
        self._ensure_log_group_exists()
        self._ensure_log_stream_exists()
        self._get_sequence_token()
        
        print(f"CloudWatch handler initialized: {self.log_group} -> {self.log_stream}")
    
    def _ensure_log_group_exists(self):
        """Create log group if it doesn't exist."""
        try:
            self.client.create_log_group(logGroupName=self.log_group)
            print(f"Created CloudWatch log group: {self.log_group}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                raise
    
    def _ensure_log_stream_exists(self):
        """Create log stream if it doesn't exist."""
        try:
            self.client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self.log_stream
            )
            print(f"Created CloudWatch log stream: {self.log_stream}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                raise
    
    def _get_sequence_token(self):
        """Get the sequence token for the log stream."""
        try:
            response = self.client.describe_log_streams(
                logGroupName=self.log_group,
                logStreamNamePrefix=self.log_stream,
                limit=1
            )
            if response['logStreams']:
                self.sequence_token = response['logStreams'][0].get('uploadSequenceToken')
        except ClientError:
            pass
    
    def emit(self, record):
        """Send log record to CloudWatch."""
        try:
            log_entry = {
                'timestamp': int(record.created * 1000),
                'message': self.format(record)
            }
            
            kwargs = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': [log_entry]
            }
            
            if self.sequence_token:
                kwargs['sequenceToken'] = self.sequence_token
            
            response = self.client.put_log_events(**kwargs)
            self.sequence_token = response.get('nextSequenceToken')
            
        except Exception as e:
            # Fall back to stderr if CloudWatch fails
            print(f"CloudWatch logging error: {e}", file=sys.stderr)


# Azure Monitor configuration is handled directly in TelemetryLogger._add_azure_handler()
# No custom handler class needed since OpenTelemetry handles the integration


class TelemetryLogger:
    """Main telemetry logger that supports multiple outputs with structured paths."""
    
    def __init__(self, service_name: str, telemetry_mode: str = None):
        self.service_name = service_name
        self.telemetry_mode = telemetry_mode or os.environ.get('TELEMETRY_MODE', 'console')
        self.env_name = os.environ.get('ENV_NAME', 'development')
        self.app_name = os.environ.get('APP_NAME', 'useless-calculator')
        
        # Create separate loggers for different data types
        self.logs_logger = logging.getLogger(f"{service_name}.logs")
        self.metrics_logger = logging.getLogger(f"{service_name}.metrics")
        self.traces_logger = logging.getLogger(f"{service_name}.traces")
        
        # Clear existing handlers to avoid duplicates
        for logger in [self.logs_logger, self.metrics_logger, self.traces_logger]:
            logger.handlers.clear()
            logger.setLevel(logging.INFO)
        
        # Parse telemetry modes
        modes = [mode.strip() for mode in self.telemetry_mode.split(',')]
        
        # Configure handlers based on modes
        for mode in modes:
            self._configure_handler(mode)
        
        # If no handlers were added, default to console
        if not self.logs_logger.handlers:
            self._add_console_handler()
        
        # Main logger points to logs logger for backward compatibility
        self.logger = self.logs_logger
    
    def _configure_handler(self, mode: str):
        """Configure handler based on mode."""
        mode = mode.lower()
        
        if mode == 'console':
            self._add_console_handler()
        elif mode == 'local':
            self._add_local_handler()
        elif mode == 'aws_cloudwatch':
            self._add_cloudwatch_handler()
        elif mode == 'azure_monitor':
            self._add_azure_handler()
        else:
            print(f"Warning: Unknown telemetry mode '{mode}', skipping", file=sys.stderr)
    
    def _add_console_handler(self):
        """Add console handler to all loggers."""
        for logger in [self.logs_logger, self.metrics_logger, self.traces_logger]:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(self._get_formatter())
            logger.addHandler(handler)
        print(f"Telemetry: Added console handler for {self.service_name}")
    
    def _add_local_handler(self):
        """Add local file handlers for structured logging."""
        # Create logs directory structure: logs/env/app/service/
        base_log_dir = Path("/logs")
        try:
            base_log_dir.mkdir(exist_ok=True)
        except (PermissionError, OSError):
            # Fallback to current directory if /logs is not writable
            base_log_dir = Path("./logs")
            print(f"Warning: /logs not accessible, using {base_log_dir.absolute()}")
        
        # Create structured directory: logs/env/app/service/
        service_log_dir = base_log_dir / self.env_name / self.app_name / self.service_name
        service_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create separate files for different data types
        handlers_config = [
            ("logs", self.logs_logger, "application.log"),
            ("metrics", self.metrics_logger, "metrics.log"),
            ("traces", self.traces_logger, "traces.log")
        ]
        
        for data_type, logger, filename in handlers_config:
            log_file = service_log_dir / filename
            
            # Use rotating file handler to prevent huge log files
            handler = RotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            handler.setFormatter(self._get_formatter())
            logger.addHandler(handler)
        
        print(f"Telemetry: Added local file handlers for {self.env_name}/{self.app_name}/{self.service_name}")
    
    def _add_cloudwatch_handler(self):
        """Add AWS CloudWatch handlers for logs, metrics, and traces."""
        try:
            # Create handlers for different data types
            handlers_config = [
                ("logs", self.logs_logger),
                ("metrics", self.metrics_logger), 
                ("traces", self.traces_logger)
            ]
            
            for data_type, logger in handlers_config:
                handler = CloudWatchHandler(self.service_name, data_type)
                handler.setFormatter(self._get_formatter())
                logger.addHandler(handler)
            
            print(f"Telemetry: Added CloudWatch handlers for {self.service_name} (AWS best practice: single log group per service)")
        except Exception as e:
            print(f"Failed to configure CloudWatch: {e}. Falling back to console.", file=sys.stderr)
            self._add_console_handler()
    
    def _add_azure_handler(self):
        """Configure Azure Monitor with OpenTelemetry instrumentation."""
        try:
            if not HAS_AZURE:
                raise ImportError(
                    "Missing Azure Monitor dependencies. Run: pip install azure-monitor-opentelemetry azure-identity azure-mgmt-monitor"
                )

            connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
            if not connection_string:
                raise ValueError("APPLICATIONINSIGHTS_CONNECTION_STRING environment variable is not set")

            self._configure_azure_monitor(connection_string)
            self._configure_log_exporter(connection_string)
            self._instrument_http_libraries()
            self._attach_fallback_loggers()
            logging.basicConfig(level=logging.INFO)

            print(f"[Telemetry] Azure Monitor configured for {self.env_name}/{self.app_name}/{self.service_name}")

        except Exception as e:
            print(f"[Telemetry] Azure Monitor setup failed: {e}. Falling back to console.", file=sys.stderr)
            self._add_console_handler()


    def _configure_azure_monitor(self, connection_string: str):
        """Initializes Azure Monitor with enriched resource attributes."""
        try:
            configure_azure_monitor(
                connection_string=connection_string,
                enable_live_metrics=True,
                resource_attributes={
                    "service.name": self.service_name,
                    "service.namespace": f"{self.env_name}.{self.app_name}",
                    "service.instance.id": f"{self.service_name}-{os.environ.get('HOSTNAME', 'unknown')}",
                    "deployment.environment": self.env_name,
                }
            )
        except Exception as err:
            # Ignore known Azure Monitor formatting issues
            if "logging_formatter" in str(err):
                print(f"[Azure Monitor] Known error ignored: {err}")
            else:
                raise


    def _instrument_http_libraries(self):
        """Activate OpenTelemetry HTTP auto-instrumentation."""
        FastAPIInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        URLLib3Instrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        print("[Telemetry] HTTP instrumentation enabled (FastAPI, requests, urllib3, httpx)")


    def _attach_fallback_loggers(self):
        """Ensure standard loggers are initialized for Azure telemetry collection."""
        for logger in [self.logs_logger, self.metrics_logger, self.traces_logger]:
            if not logger.hasHandlers():
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(self._get_formatter())
                logger.addHandler(handler)


    def _configure_log_exporter(self, connection_string: str):
        """Enable OpenTelemetry log export to Azure Monitor."""
        try:
            # from opentelemetry.sdk._logs import LoggerProvider
            # from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
            # from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
            # from opentelemetry._logs import set_logger_provider
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk._logs import LoggerProvider
            from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
            from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
            from opentelemetry._logs import set_logger_provider

            resource = Resource.create({
                "service.name": self.service_name,
                "service.namespace": f"{self.env_name}.{self.app_name}",
                "service.instance.id": f"{self.service_name}-{os.environ.get('HOSTNAME', 'unknown')}",
                "deployment.environment": self.env_name,
            })            

            provider = LoggerProvider(resource=resource)
            exporter = AzureMonitorLogExporter(connection_string=connection_string)
            processor = BatchLogRecordProcessor(exporter)
            provider.add_log_record_processor(processor)
            set_logger_provider(provider)

            print("[Telemetry] Azure Monitor log exporter configured")
        except Exception as e:
            print(f"[Telemetry] Failed to configure log exporter: {e}", file=sys.stderr)

    def _get_formatter(self):
        """Get log formatter with environment context."""
        return logging.Formatter(
            f'%(asctime)s - {self.env_name}/{self.app_name}/%(name)s - %(levelname)s - %(message)s - '
            '[%(filename)s:%(lineno)d] - %(funcName)s()'
        )
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger."""
        return self.logger
    
    def log_metrics(self, metrics: Dict[str, Any]):
        """Log metrics in a structured format."""
        # Add environment context to metrics
        enhanced_metrics = {
            **metrics,
            "env_name": self.env_name,
            "app_name": self.app_name,
            "service_name": self.service_name,
            "timestamp": datetime.now().isoformat()
        }
        self.metrics_logger.info(f"METRICS: {json.dumps(enhanced_metrics)}")
    
    def log_trace(self, trace_id: str, span_id: str, operation: str, duration_ms: float, metadata: Dict[str, Any] = None):
        """Log trace information."""
        trace_data = {
            "trace_id": trace_id,
            "span_id": span_id,
            "operation": operation,
            "duration_ms": duration_ms,
            "service": self.service_name,
            "env_name": self.env_name,
            "app_name": self.app_name,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.traces_logger.info(f"TRACE: {json.dumps(trace_data)}")
    
    def log_error_with_trace(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with full stack trace."""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "service": self.service_name,
            "env_name": self.env_name,
            "app_name": self.app_name,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        self.logs_logger.error(f"ERROR_TRACE: {json.dumps(error_data)}")


# Convenience function to create logger
def create_telemetry_logger(service_name: str) -> TelemetryLogger:
    """Create a telemetry logger for a service."""
    return TelemetryLogger(service_name)


# Example usage and testing
if __name__ == "__main__":
    # Test the telemetry logger
    logger = create_telemetry_logger("test-service")
    log = logger.get_logger()
    
    # Test different log levels
    log.info("This is an info message")
    log.warning("This is a warning message")
    log.error("This is an error message")
    
    # Test metrics
    logger.log_metrics({
        "requests_per_second": 150,
        "response_time_ms": 23.5,
        "error_rate": 0.02
    })
    
    # Test trace
    logger.log_trace(
        trace_id="abc123",
        span_id="def456",
        operation="calculate_addition",
        duration_ms=15.3,
        metadata={"first_number": 5, "second_number": 3}
    )
    
    # Test error with trace
    try:
        1 / 0
    except Exception as e:
        logger.log_error_with_trace(e, {"operation": "division", "values": [1, 0]})