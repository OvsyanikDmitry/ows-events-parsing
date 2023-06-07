FROM python:3.11

WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY root/ /app

CMD ["uvicorn", "root.server:app", "--host", "0.0.0.0", "--port", "80"]
