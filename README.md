# s3-photos-viewer
Simple docker image to view photos resides in AWS S3 Bucket.


## Prerequisites

1. Create S3 Bucket, my-bucket
2. Create IAM user with only allow ready-only s3 access, no console login, iam policy have following template


  ```bash
{
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetObject"
        ]
        Resource = [
          "arn:aws:s3:::my-bucket",
          "arn:aws:s3:::my-bucket/*"
        ]
      }
    ]
}    
  ```
3. Create AUTH_KEY with following format

  ```bash
  <aws_access_key_id>:<aws_secret_access_key>
  ```

## How to build
docker build -t s3-photos-viewer .
## How to run
  ```bash
docker run -p 8080:8080 \
           -e BUCKET=<your-aws-s3-bucket> \
           -e AUTH_KEY=<your-aws-iam-access-key-id>:<your-aws-iam-secret-access-key> \
           s3-photos-viewer
  ```
				 		   
