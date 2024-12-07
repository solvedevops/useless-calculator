FROM alpine

RUN apk add --update python3 py3-pip

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --break-system-packages --upgrade -r /app/requirements.txt

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--proxy-headers"]
