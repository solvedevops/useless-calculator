from fastapi import FastAPI, Request, Form, HTTPException
import requests
import os
import time
import uuid
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from telemetry import create_telemetry_logger
#from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Initialize telemetry
telemetry = create_telemetry_logger("useless-calculator")
logger = telemetry.get_logger()

# Response model for health check
class HealthCheck(BaseModel):
    status: str
    service: str
    dependencies: dict

app = FastAPI(
    title="Useless Calculator",
    description="Main calculator service that orchestrates mathematical operations",
    version="2.0.0"
)
#FastAPIInstrumentor().instrument_app(app)

app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

ADDURLENDPOINT = os.environ.get('ADD_URL_ENDPOINT')
DIVIDEURLENDPOINT = os.environ.get('DIVIDE_URL_ENDPOINT')
MULTIURLENDPOINT = os.environ.get('MULTI_URL_ENDPOINT')
SUBURLENDPOINT = os.environ.get('SUB_URL_ENDPOINT')

# Check if all required endpoints are configured
if not all([ADDURLENDPOINT, DIVIDEURLENDPOINT, MULTIURLENDPOINT, SUBURLENDPOINT]):
    logger.warning("Some service endpoints are not configured. Please set all environment variables.")

#---- index render
@app.get("/", tags=["UI"])
async def index_page(request: Request):
    """Render the main calculator page."""
    logger.info("Rendering index page")
    return templates.TemplateResponse("index.html", {"request": request})

#---- addition render
@app.get("/add", tags=["UI"])
async def addition_page(request: Request):
    """Render the addition page."""
    show = 0
    return templates.TemplateResponse("add.html", {"request": request, "show": show})

@app.post("/add", tags=["Operations"])
async def perform_addition(request: Request, First_Number: float = Form(None), Second_Number: float = Form(None)):
    """Perform addition operation by calling the addition microservice."""
    if First_Number is None or Second_Number is None:
        show = 0
        return templates.TemplateResponse("add.html", {"request": request, "show": show, "error": "Please enter both numbers"})
    
    # Start trace
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"Performing addition: {First_Number} + {Second_Number}")
        response = requests.get(ADDURLENDPOINT, params={"first_number": First_Number, "second_number": Second_Number}, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        answer = result["result"] if isinstance(result, dict) else result
        duration_ms = (time.time() - start_time) * 1000
        
        # Log trace
        telemetry.log_trace(
            trace_id=trace_id,
            span_id=span_id,
            operation="calculator_addition",
            duration_ms=duration_ms,
            metadata={
                "first_number": First_Number,
                "second_number": Second_Number,
                "result": answer,
                "service_called": "addition-service"
            }
        )
        
        # Log metrics
        telemetry.log_metrics({
            "operation": "calculator_addition",
            "success": True,
            "response_time_ms": duration_ms
        })
        
        show = 1
        return templates.TemplateResponse("add.html", {"request": request, "answer": answer, "show": show})
    except requests.exceptions.Timeout:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Addition service timeout")
        telemetry.log_metrics({
            "operation": "calculator_addition",
            "error_type": "timeout",
            "response_time_ms": duration_ms
        })
        return templates.TemplateResponse("add.html", {"request": request, "show": 0, "error": "Service timeout. Please try again."})
    except requests.exceptions.RequestException as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Addition service error: {str(e)}")
        telemetry.log_error_with_trace(e, {
            "operation": "calculator_addition",
            "service": "addition-service",
            "duration_ms": duration_ms
        })
        return templates.TemplateResponse("add.html", {"request": request, "show": 0, "error": "Service unavailable. Please try again later."})
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Unexpected error in addition: {str(e)}")
        telemetry.log_error_with_trace(e, {
            "operation": "calculator_addition",
            "duration_ms": duration_ms
        })
        return templates.TemplateResponse("add.html", {"request": request, "show": 0, "error": "An error occurred. Please try again."})

#---- divide render
@app.get("/divide", tags=["UI"])
async def division_page(request: Request):
    """Render the division page."""
    show = 0
    return templates.TemplateResponse("divide.html", {"request": request, "show": show})

@app.post("/divide", tags=["Operations"])
async def perform_division(request: Request, First_Number: float = Form(None), Second_Number: float = Form(None)):
    """Perform division operation by calling the division microservice."""
    if First_Number is None or Second_Number is None:
        show = 0
        return templates.TemplateResponse("divide.html", {"request": request, "show": show, "error": "Please enter both numbers"})
    
    # Start trace
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"Performing division: {First_Number} / {Second_Number}")
        response = requests.get(DIVIDEURLENDPOINT, params={"first_number": First_Number, "second_number": Second_Number}, timeout=5)
        
        if response.status_code == 400:
            duration_ms = (time.time() - start_time) * 1000
            error_detail = response.json().get("detail", "Invalid input")
            telemetry.log_metrics({
                "operation": "calculator_division",
                "error_type": "validation_error",
                "response_time_ms": duration_ms
            })
            return templates.TemplateResponse("divide.html", {"request": request, "show": 0, "error": error_detail})
        
        response.raise_for_status()
        
        result = response.json()
        answer = result["result"] if isinstance(result, dict) else result
        duration_ms = (time.time() - start_time) * 1000
        
        # Log trace
        telemetry.log_trace(
            trace_id=trace_id,
            span_id=span_id,
            operation="calculator_division",
            duration_ms=duration_ms,
            metadata={
                "first_number": First_Number,
                "second_number": Second_Number,
                "result": answer,
                "service_called": "division-service"
            }
        )
        
        # Log metrics
        telemetry.log_metrics({
            "operation": "calculator_division",
            "success": True,
            "response_time_ms": duration_ms
        })
        
        show = 1
        return templates.TemplateResponse("divide.html", {"request": request, "answer": answer, "show": show})
    except requests.exceptions.Timeout:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Division service timeout")
        telemetry.log_metrics({
            "operation": "calculator_division",
            "error_type": "timeout",
            "response_time_ms": duration_ms
        })
        return templates.TemplateResponse("divide.html", {"request": request, "show": 0, "error": "Service timeout. Please try again."})
    except requests.exceptions.RequestException as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Division service error: {str(e)}")
        telemetry.log_error_with_trace(e, {
            "operation": "calculator_division",
            "service": "division-service",
            "duration_ms": duration_ms
        })
        return templates.TemplateResponse("divide.html", {"request": request, "show": 0, "error": "Service unavailable. Please try again later."})
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Unexpected error in division: {str(e)}")
        telemetry.log_error_with_trace(e, {
            "operation": "calculator_division",
            "duration_ms": duration_ms
        })
        return templates.TemplateResponse("divide.html", {"request": request, "show": 0, "error": "An error occurred. Please try again."})

#---- multi render
@app.get("/multi", tags=["UI"])
async def multiplication_page(request: Request):
    """Render the multiplication page."""
    show = 0
    return templates.TemplateResponse("multi.html", {"request": request, "show": show})

@app.post("/multi", tags=["Operations"])
async def perform_multiplication(request: Request, First_Number: float = Form(None), Second_Number: float = Form(None)):
    """Perform multiplication operation by calling the multiplication microservice."""
    if First_Number is None or Second_Number is None:
        show = 0
        return templates.TemplateResponse("multi.html", {"request": request, "show": show, "error": "Please enter both numbers"})
    
    # Start trace
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"Performing multiplication: {First_Number} * {Second_Number}")
        response = requests.get(MULTIURLENDPOINT, params={"first_number": First_Number, "second_number": Second_Number}, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        answer = result["result"] if isinstance(result, dict) else result
        duration_ms = (time.time() - start_time) * 1000
        
        # Log trace
        telemetry.log_trace(
            trace_id=trace_id,
            span_id=span_id,
            operation="calculator_multiplication",
            duration_ms=duration_ms,
            metadata={
                "first_number": First_Number,
                "second_number": Second_Number,
                "result": answer,
                "service_called": "multiplication-service"
            }
        )
        
        # Log metrics
        telemetry.log_metrics({
            "operation": "calculator_multiplication",
            "success": True,
            "response_time_ms": duration_ms
        })
        
        show = 1
        return templates.TemplateResponse("multi.html", {"request": request, "answer": answer, "show": show})
    except requests.exceptions.Timeout:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Multiplication service timeout")
        telemetry.log_metrics({
            "operation": "calculator_multiplication",
            "error_type": "timeout",
            "response_time_ms": duration_ms
        })
        return templates.TemplateResponse("multi.html", {"request": request, "show": 0, "error": "Service timeout. Please try again."})
    except requests.exceptions.RequestException as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Multiplication service error: {str(e)}")
        telemetry.log_error_with_trace(e, {
            "operation": "calculator_multiplication",
            "service": "multiplication-service",
            "duration_ms": duration_ms
        })
        return templates.TemplateResponse("multi.html", {"request": request, "show": 0, "error": "Service unavailable. Please try again later."})
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Unexpected error in multiplication: {str(e)}")
        telemetry.log_error_with_trace(e, {
            "operation": "calculator_multiplication",
            "duration_ms": duration_ms
        })
        return templates.TemplateResponse("multi.html", {"request": request, "show": 0, "error": "An error occurred. Please try again."})

#---- sub render
@app.get("/sub", tags=["UI"])
async def subtraction_page(request: Request):
    """Render the subtraction page."""
    show = 0
    return templates.TemplateResponse("sub.html", {"request": request, "show": show})

@app.post("/sub", tags=["Operations"])
async def perform_subtraction(request: Request, First_Number: float = Form(None), Second_Number: float = Form(None)):
    """Perform subtraction operation by calling the subtraction microservice."""
    if First_Number is None or Second_Number is None:
        show = 0
        return templates.TemplateResponse("sub.html", {"request": request, "show": show, "error": "Please enter both numbers"})
    
    # Start trace
    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"Performing subtraction: {First_Number} - {Second_Number}")
        response = requests.get(SUBURLENDPOINT, params={"first_number": First_Number, "second_number": Second_Number}, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        answer = result["result"] if isinstance(result, dict) else result
        duration_ms = (time.time() - start_time) * 1000
        
        # Log trace
        telemetry.log_trace(
            trace_id=trace_id,
            span_id=span_id,
            operation="calculator_subtraction",
            duration_ms=duration_ms,
            metadata={
                "first_number": First_Number,
                "second_number": Second_Number,
                "result": answer,
                "service_called": "subtraction-service"
            }
        )
        
        # Log metrics
        telemetry.log_metrics({
            "operation": "calculator_subtraction",
            "success": True,
            "response_time_ms": duration_ms
        })
        
        show = 1
        return templates.TemplateResponse("sub.html", {"request": request, "answer": answer, "show": show})
    except requests.exceptions.Timeout:
        duration_ms = (time.time() - start_time) * 1000
        logger.error("Subtraction service timeout")
        telemetry.log_metrics({
            "operation": "calculator_subtraction",
            "error_type": "timeout",
            "response_time_ms": duration_ms
        })
        return templates.TemplateResponse("sub.html", {"request": request, "show": 0, "error": "Service timeout. Please try again."})
    except requests.exceptions.RequestException as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Subtraction service error: {str(e)}")
        telemetry.log_error_with_trace(e, {
            "operation": "calculator_subtraction",
            "service": "subtraction-service",
            "duration_ms": duration_ms
        })
        return templates.TemplateResponse("sub.html", {"request": request, "show": 0, "error": "Service unavailable. Please try again later."})
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Unexpected error in subtraction: {str(e)}")
        telemetry.log_error_with_trace(e, {
            "operation": "calculator_subtraction",
            "duration_ms": duration_ms
        })
        return templates.TemplateResponse("sub.html", {"request": request, "show": 0, "error": "An error occurred. Please try again."})

#---- health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["health"])
async def health_check():
    """Health check endpoint to verify service and dependencies are running."""
    start_time = time.time()
    dependencies = {
        "addition-service": "unknown",
        "subtraction-service": "unknown",
        "multiplication-service": "unknown",
        "division-service": "unknown"
    }
    
    # Check each dependency
    services = [
        ("addition-service", ADDURLENDPOINT),
        ("subtraction-service", SUBURLENDPOINT),
        ("multiplication-service", MULTIURLENDPOINT),
        ("division-service", DIVIDEURLENDPOINT)
    ]
    
    for service_name, endpoint in services:
        if endpoint:
            try:
                response = requests.get(f"{endpoint}/health", timeout=2)
                dependencies[service_name] = "healthy" if response.status_code == 200 else "unhealthy"
            except:
                dependencies[service_name] = "unreachable"
        else:
            dependencies[service_name] = "not_configured"
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Log health check metrics
    telemetry.log_metrics({
        "health_check": 1,
        "service": "useless-calculator",
        "dependencies_healthy": sum(1 for v in dependencies.values() if v == "healthy"),
        "dependencies_total": len(dependencies),
        "response_time_ms": duration_ms
    })
    
    logger.info(f"Health check completed: {dependencies}")
    
    return {
        "status": "healthy",
        "service": "useless-calculator",
        "dependencies": dependencies
    }
