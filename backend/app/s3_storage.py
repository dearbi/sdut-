import os
import boto3
from typing import Dict

def _client():
    return boto3.client(
        's3',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    )

def upload_bytes(bucket: str, key: str, data: bytes, content_type: str = 'image/png') -> Dict[str, str]:
    s3 = _client()
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    url = f"https://{bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{key}"
    return {"bucket": bucket, "key": key, "url": url}

def ensure_lifecycle(bucket: str, days: int = 30):
    s3 = _client()
    cfg = {
        'Rules': [{
            'ID': 'auto-expire-temp-objects',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'processed/'},
            'Expiration': {'Days': days}
        }]
    }
    s3.put_bucket_lifecycle_configuration(Bucket=bucket, LifecycleConfiguration=cfg)