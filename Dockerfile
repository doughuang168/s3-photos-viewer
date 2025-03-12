FROM python:3.9-slim

RUN pip install flask boto3 python-dotenv

RUN mkdir -p /usr/src/s3-photos-viewer
WORKDIR      /usr/src/s3-photos-viewer
COPY .       /usr/src/s3-photos-viewer/

RUN adduser -u 5678 --disabled-password --gecos "" s3-photos-viewer \
           && chown -R s3-photos-viewer:s3-photos-viewer /usr/src/s3-photos-viewer \
           && chown -R s3-photos-viewer:s3-photos-viewer /usr/local

# Switch to the non-privileged user to run the application.
USER s3-photos-viewer

EXPOSE 8080

CMD ["python", "app.py"]
