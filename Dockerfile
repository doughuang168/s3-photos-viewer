FROM python:3.9-slim

WORKDIR /app

RUN pip install flask boto3 python-dotenv

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
