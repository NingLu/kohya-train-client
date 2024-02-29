import boto3
import requests
import argparse
from botocore.exceptions import NoCredentialsError

def generate_presigned_url(bucket_name, object_key, expiration_seconds=7200):
    """
    Generates a presigned URL for downloading an object from an S3 bucket.

    :param bucket_name: Name of the S3 bucket.
    :param object_key: Key (filename) of the object to be accessed.
    :param expiration_seconds: Expiration time for the URL (default is 1 hour).
    :return: Presigned URL.
    """
    try:
        s3_client = boto3.client('s3')
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration_seconds
        )
        return url
    except NoCredentialsError:
        print("Error: AWS credentials not found. Make sure you have configured your credentials.")
        return None

def download_file_from_url(url, local_file_name):
    """
    Downloads a file from a given URL and saves it locally.

    :param url: URL of the file to download.
    :param local_file_name: Name of the local file to save.
    """
    try:
        response = requests.get(url)
        with open(local_file_name, 'wb') as local_file:
            local_file.write(response.content)
        print(f"File downloaded and saved as {local_file_name}")
    except requests.RequestException as e:
        print(f"Error downloading file: {e}")

if __name__ == "__main__":
    bucket_name = 'your_bucket_name' # Replace with your actual bucket name
    object_key = 'your_object_key'  # Replace with your actual object key, such as access_log_2024022910_14.zip
    # The client which has S3 access generates presigned url and
    # pass it to the client which doesn't have S3 access
    presigned_url = generate_presigned_url(bucket_name, object_key)
    if presigned_url:
        local_file_name = object_key.split('/')[-1]
        download_file_from_url(presigned_url, local_file_name)
    else:
        print("Failed to generate presigned URL.")
