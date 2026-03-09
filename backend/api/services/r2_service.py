import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "ads")

# Cloudflare R2 endpoint format: https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Public custom domain or R2.dev subdomain if you have one configured
# e.g., "https://pub-xxxxxxxxxx.r2.dev"
R2_PUBLIC_URL_PREFIX = os.getenv("R2_PUBLIC_URL_PREFIX", "")

def get_r2_client():
    if not R2_ACCOUNT_ID or not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY:
        raise ValueError("Missing Cloudflare R2 credentials in .env")
    
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto" # Cloudflare R2 uses 'auto'
    )

async def upload_file_to_r2(filename: str, content: bytes, content_type: str) -> str:
    """
    Uploads a file to Cloudflare R2 and returns the public URL.
    """
    s3 = get_r2_client()
    
    try:
        s3.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=filename,
            Body=content,
            ContentType=content_type
        )
        
        # If public prefix is set, return the clean public URL
        if R2_PUBLIC_URL_PREFIX:
            return f"{R2_PUBLIC_URL_PREFIX}/{filename}"
        
        # If no public domain, generate a presigned URL (valid for 1 hour by default, up to 7 days)
        # Note: Since the dashboard needs persistent access, it is HIGHLY recommended to 
        # enable public access or a custom domain on the R2 bucket for these files.
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': R2_BUCKET_NAME, 'Key': filename},
            ExpiresIn=604800 # 7 days
        )
        return url
    except ClientError as e:
        print(f"Error uploading to R2: {e}")
        raise e
