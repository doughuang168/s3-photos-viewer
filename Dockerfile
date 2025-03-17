# Use the AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.9

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Set the entry point for Lambda
CMD ["app.handler"]
