FROM alpine

RUN apk add --update python3 py3-pip

WORKDIR /app

COPY . /app
#COPY ./app.py /app

#COPY ./templates /app/

#COPY ./requirements.txt /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--proxy-headers"]
