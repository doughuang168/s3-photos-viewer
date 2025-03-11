FROM python:3.9-slim

WORKDIR /app

RUN pip install flask boto3 python-dotenv

RUN adduser -u 5678 --disabled-password --gecos "" s3-photos-viewer \
           && chown -R s3-photos-viewer:s3-photos-viewer /usr/src/s3-photos-viewer \
           && chown -R s3-photos-viewer:s3-photos-viewer /usr/local

USER s3-photos-viewer

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
