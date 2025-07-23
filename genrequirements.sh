#!/bin/bash

# Check if no arguments provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 {alpine|aws-logs|azure-logs}"
    echo "Generates requirements.txt file based on the specified configuration"
    exit 1
fi

# Get the first argument
CONFIG=$1

# Function to write alpine requirements
write_alpine_requirements() {
    cat > requirements.txt << 'EOF'
# Core dependencies
fastapi==0.115.6
uvicorn[standard]==0.32.1
jinja2==3.1.4
python-multipart==0.0.19
requests==2.32.3
# Testing
pytest==8.3.0
httpx==0.27.0
EOF
}

# Function to write aws-logs requirements
write_aws_logs_requirements() {
    cat > requirements.txt << 'EOF'
# Core dependencies
fastapi==0.115.6
uvicorn[standard]==0.32.1
jinja2==3.1.4
python-multipart==0.0.19
requests==2.32.3
# Testing
pytest==8.3.0
httpx==0.27.0
# Optional cloud telemetry dependencies
# For AWS CloudWatch
boto3==1.34.0
EOF
}

# Function to write azure-logs requirements
write_azure_logs_requirements() {
    cat > requirements.txt << 'EOF'
# Core dependencies
fastapi==0.115.6
uvicorn[standard]==0.32.1
jinja2==3.1.4
python-multipart==0.0.19
requests==2.32.3
# Testing
pytest==8.3.0
httpx==0.27.0
# Optional cloud telemetry dependencies
# For Azure Monitor with HTTP instrumentation
azure-monitor-opentelemetry
azure-identity==1.23.1
azure-mgmt-monitor==6.0.2
azure-monitor-opentelemetry-exporter==1.0.0b40
opentelemetry-sdk==1.31.1
opentelemetry-api==1.31.1
opentelemetry-instrumentation-fastapi
opentelemetry-instrumentation-requests
opentelemetry-instrumentation-urllib3
opentelemetry-instrumentation-httpx
EOF

sed -i.bak 's/^#from opentelemetry\.instrumentation\.fastapi import FastAPIInstrumentor$/from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor/; s/^#FastAPIInstrumentor()\.instrument_app(app)$/FastAPIInstrumentor().instrument_app(app)/' app.py && rm app.py.bak
}

# Process the configuration argument
case $CONFIG in
    alpine)
        write_alpine_requirements
        echo "Generated requirements.txt for alpine configuration"
        ;;
    aws-logs)
        write_aws_logs_requirements
        echo "Generated requirements.txt for aws-logs configuration"
        ;;
    azure-logs)
        write_azure_logs_requirements
        echo "Generated requirements.txt for azure-logs configuration"
        ;;
    *)
        echo "Error: Invalid argument '$CONFIG'"
        echo "Usage: $0 {alpine|aws-logs|azure-logs}"
        exit 1
        ;;
esac

exit 0