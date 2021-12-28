# Useless Calculator Project

This project is a demo used in microservice deployment training. As you might have guessed, the app is pretty useless and definitely buggy. 
DO NOT TAKE IT TO PROD, except in a demo environment.

The other microservices that make this project complete are;
- [Addition Service](https://github.com/solvedevops/addition-service)
- [Division Service](https://github.com/solvedevops/division-service)
- [Multiplication Service](https://github.com/solvedevops/multiplication-service)
- [Subtration Service](https://github.com/solvedevops/subtraction-service)

You are free to use it how ever you please.

### TechStack
- FastApi
- Python
- HTML
- Bootstrap

### Quick Start
Using docker-compose, you can bring up all the services in one go;

    docker-compose up -d

Or if you decide to bring the services up any other way, remember to set the service urls for discovery on the "useless calculator" service;

    - ADD_URL_ENDPOINT=http://addition-service:5000
    - DIVIDE_URL_ENDPOINT=http://division-service:5000
    - MULTI_URL_ENDPOINT=http://multiplication-service:5000
    - SUB_URL_ENDPOINT=http://subtraction-service:5000 


###  Screenshots

![Addition Screenshot](templates/static/images/addition.png)


![Division Screenshot](templates/static/images/division.png)
