# s3-photos-viewer
Simple docker image to view photos resides in AWS S3 Bucket.


## Prerequisites

1. Create S3 Bucket, my-bucket
2. Create IAM role with ready-only s3 access, no console login, iam policy have following template


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
3. Create AUTH_KEY
