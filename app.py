from fastapi import FastAPI, Request, Form
import requests
import os
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

ADDURLENDPOINT = os.environ.get('ADD_URL_ENDPOINT')
DIVIDEURLENDPOINT = os.environ.get('DIVIDE_URL_ENDPOINT')
MULTIURLENDPOINT = os.environ.get('MULTI_URL_ENDPOINT')
SUBURLENDPOINT = os.environ.get('SUB_URL_ENDPOINT')

#---- index render
@app.get("/")
async def add_blank(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#---- addition render
@app.get("/add")
async def add_blank(request: Request):
    show = 0
    return templates.TemplateResponse("add.html", {"request": request, "show": show})

@app.post("/add")
async def parse_data(request: Request, First_Number: int = Form(None), Second_Number: int = Form(None)):
    if not First_Number or not Second_Number:
        show = 0
        return templates.TemplateResponse("add.html", {"request": request, "show": show})
    else:
        show = 1
        ans = requests.get(ADDURLENDPOINT, params={"first_number": First_Number, "second_number": Second_Number})
        return templates.TemplateResponse("add.html", {"request": request, "answer": ans.text, "show": show})

#---- divide render
@app.get("/divide")
async def add_blank(request: Request):
    show = 0
    return templates.TemplateResponse("divide.html", {"request": request, "show": show})

@app.post("/divide")
async def parse_data(request: Request, First_Number: int = Form(None), Second_Number: int = Form(None)):
    if not First_Number or not Second_Number:
        show = 0
        return templates.TemplateResponse("divide.html", {"request": request, "show": show})
    else:
        show = 1
        ans = requests.get(DIVIDEURLENDPOINT, params={"first_number": First_Number, "second_number": Second_Number})
        return templates.TemplateResponse("divide.html", {"request": request, "answer": ans.text, "show": show})

#---- multi render
@app.get("/multi")
async def add_blank(request: Request):
    show = 0
    return templates.TemplateResponse("multi.html", {"request": request, "show": show})

@app.post("/multi")
async def parse_data(request: Request, First_Number: int = Form(None), Second_Number: int = Form(None)):
    if not First_Number or not Second_Number:
        show = 0
        return templates.TemplateResponse("multi.html", {"request": request, "show": show})
    else:
        show = 1
        ans = requests.get(MULTIURLENDPOINT, params={"first_number": First_Number, "second_number": Second_Number})
        return templates.TemplateResponse("multi.html", {"request": request, "answer": ans.text, "show": show})

#---- sub render
@app.get("/sub")
async def add_blank(request: Request):
    show = 0
    return templates.TemplateResponse("sub.html", {"request": request, "show": show})

@app.post("/sub")
async def parse_data(request: Request, First_Number: int = Form(None), Second_Number: int = Form(None)):
    if not First_Number or not Second_Number:
        show = 0
        return templates.TemplateResponse("sub.html", {"request": request, "show": show})
    else:
        show = 1
        ans = requests.get(SUBURLENDPOINT, params={"first_number": First_Number, "second_number": Second_Number})
        return templates.TemplateResponse("sub.html", {"request": request, "answer": ans.text, "show": show})
