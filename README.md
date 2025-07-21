# Useless Calculator - Main Application

This is the main orchestrator service for the Useless Calculator microservices demo. It provides a web interface for performing basic mathematical operations by calling dedicated microservices.

**⚠️ DEMO PROJECT WARNING**: This application is designed for demonstration and training purposes only. It is intentionally buggy and should **NOT** be used in production environments. You have been warned.

## 🏗️ Architecture

The main calculator service orchestrates calls to four mathematical operation microservices:
- [Addition Service](https://github.com/solvedevops/addition-service) - Handles addition operations
- [Subtraction Service](https://github.com/solvedevops/subtraction-service) - Handles subtraction operations  
- [Multiplication Service](https://github.com/solvedevops/multiplication-service) - Handles multiplication operations
- [Division Service](https://github.com/solvedevops/division-service) - Handles division operations

## 🛠️ Technology Stack

- **FastAPI** - Modern Python web framework
- **Jinja2** - HTML templating engine
- **Bootstrap 5.1.3** - Frontend CSS framework (locally stored)
- **Python 3.7+** - Programming language
- **Docker** - Containerization

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access the application:**
   ```
   http://localhost
   ```

3. **Stop all services:**
   ```bash
   docker-compose down
   ```

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export ADD_URL_ENDPOINT=http://localhost:5001
   export DIVIDE_URL_ENDPOINT=http://localhost:5002
   export MULTI_URL_ENDPOINT=http://localhost:5003
   export SUB_URL_ENDPOINT=http://localhost:5004
   export ENV_NAME=development
   export APP_NAME=useless-calculator
   export TELEMETRY_MODE=console
   ```

3. **Run the application:**
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 5000
   ```

## ⚙️ Configuration

### Required Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ADD_URL_ENDPOINT` | Yes | None | URL for addition service |
| `DIVIDE_URL_ENDPOINT` | Yes | None | URL for division service |
| `MULTI_URL_ENDPOINT` | Yes | None | URL for multiplication service |
| `SUB_URL_ENDPOINT` | Yes | None | URL for subtraction service |
| `ENV_NAME` | Yes | `development` | Environment identifier |
| `APP_NAME` | Yes | `useless-calculator` | Application identifier |

### Telemetry Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEMETRY_MODE` | No | `console` | Logging destination |
| `AWS_DEFAULT_REGION` | CloudWatch | `us-east-1` | AWS region for CloudWatch |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Azure | None | Azure Monitor connection |

#### Telemetry Modes

```bash
# Console output (default)
TELEMETRY_MODE=console

# Local file logging (structured: logs/env/app/service/)
TELEMETRY_MODE=local

# AWS CloudWatch (See section about container tags below)
TELEMETRY_MODE=aws_cloudwatch

# Azure Monitor (See section about container tags below)
TELEMETRY_MODE=azure_monitor

# Multiple outputs
TELEMETRY_MODE=console,local
TELEMETRY_MODE=console,aws_cloudwatch
```

## 📊 Monitoring & Observability

### Structured Telemetry

The application provides comprehensive observability with structured logging:

- **Logs**: Application events and errors
- **Metrics**: Performance and operational metrics
- **Traces**: Request flow across services

#### Cloud Integration (See section about container tags below)

**AWS CloudWatch:**
- Log Groups: `/{ENV_NAME}/{APP_NAME}/{logs|metrics|traces}`
- Log Streams: `{SERVICE_NAME}/{HOSTNAME}/{YYYY/MM/DD}`

**Required Permissions:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```


**Azure Monitor:**
- Types: logs, metrics, traces

### Health Check

```bash
curl http://localhost/health
```

Returns service status and dependency health.

### API Documentation

Access auto-generated API documentation:
- **Swagger UI**: http://localhost/docs
- **ReDoc**: http://localhost/redoc

## 🏃‍♂️ Usage Examples

### Basic Operations

1. **Addition**: Navigate to http://localhost/add
2. **Subtraction**: Navigate to http://localhost/sub  
3. **Multiplication**: Navigate to http://localhost/multi
4. **Division**: Navigate to http://localhost/divide

### Example API Calls

```bash
# Health check
curl http://localhost/health

# Addition via form (browser)
# Visit: http://localhost/add
# Enter: First Number = 5, Second Number = 3
# Result: 8

# All operations support decimal numbers
```

## 🔧 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest test_app.py -v
```

### Static Assets

All static assets are stored locally for offline compatibility:
- **CSS**: `templates/static/css/`
- **JavaScript**: `templates/static/js/`  
- **Images**: `templates/static/images/`
- **Icons**: Favicons and PWA icons included

No external CDN dependencies - works in locked down environments.

### Docker Build

```bash
# Build custom image
docker build -t my-useless-calculator .

# Run with custom image (note service ports)
docker run -p 80:5000 \
  -e ENV_NAME=development \
  -e APP_NAME=useless-calculator \
  -e TELEMETRY_MODE=console \
  -e ADD_URL_ENDPOINT=http://addition-service:5001 \
  -e DIVIDE_URL_ENDPOINT=http://division-service:5001 \
  -e MULTI_URL_ENDPOINT=http://multiplication-service:5003 \
  -e SUB_URL_ENDPOINT=http://subtraction-service:5004 \
  my-useless-calculator
```

## Container tags
In order to keep the containers small, the default tag :latest includes only local and console storage for logs, metrics and traces.
To demo cloud provide storage for logs, metrics and traces use the following tags. You still have to pass the TELEMETRY_MODE= env variable

:latest for console and local storage
:aws-logs for cloudwatch configuration (You need IAM for this to work)
:azure-logs for Azure monitor (You need connection string for Azure monitor for this to work)

## 📁 Project Structure

```
useless-calculator/
├── app.py                 # Main FastAPI application
├── telemetry.py          # Telemetry and logging module
├── test_app.py           # Unit tests
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Multi-service orchestration
├── templates/           # HTML templates and static assets
│   ├── *.html          # Jinja2 templates
│   └── static/         # Local static assets
│       ├── css/        # Bootstrap CSS and custom styles
│       ├── js/         # Bootstrap JavaScript
│       └── images/     # Icons and images
└── manifests/          # Kubernetes deployment files
    ├── deployment.yaml
    └── service.yaml
```

## 🔐 Security Notes

- No sensitive data is logged
- Input validation prevents basic injection
- Static assets served locally (no external dependencies)
- Health checks don't expose sensitive information

## 📚 Related Services

- [Addition Service](https://github.com/solvedevops/addition-service) - Handles addition operations
- [Subtraction Service](https://github.com/solvedevops/subtraction-service) - Handles subtraction operations  
- [Multiplication Service](https://github.com/solvedevops/multiplication-service) - Handles multiplication operations
- [Division Service](https://github.com/solvedevops/division-service) - Handles division operations

## ⚖️ License

This project is for educational and demonstration purposes. Use at your own risk in demo environments only.

## 🤝 Contributing

This is a demo project for training purposes. Feel free to fork and experiment! Attributions Welcome!