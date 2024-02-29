import argparse
import json
import os
import sys
import boto3
import requests
sys.path.append("../")
import time
from shared.api_endpoint import ApiEndpoint


parser = argparse.ArgumentParser(description="Upload datasets from local to S3, create a training job and wait the job completed")
parser.add_argument("--api_url", required=True, help="API endpoint url of the solution, you can get it from CloudFormation stack's output, eg. https://example.execute-api.us-east-1.amazonaws.com/prod/")
parser.add_argument("--api_key", required=True, help="API key of the solution, you can get it from CloudFormation stack's output")
parser.add_argument("--creator", required=True, help="User name to invoke training, the user is created by WebUI or API, eg. admin")
parser.add_argument("--model_s3_path", required=True, help="S3 path to store your model file, model can be uploaded to S3 by WebUI, eg. s3://example/Stable-diffusion/checkpoint/custom/05de5ff6-409d-4fd5-a59a-5c58f8fb2d04/v1-5-pruned-emaonly.safetensors")
parser.add_argument("--dataset_local_folder_path", required=True, help="Local folder path of your dataset, eg. /Users/example/10_demo. The script uploads the dataset from your local folder to S3 bucket")
parser.add_argument("--s3_bucket_name", required=True, help="S3 bucket name to store your dataset, eg. dataset-bucket. The script uploads the dataset from your local folder to this bucket")
parser.add_argument("--s3_prefix", required=True, help="S3 prefix to store your dataset, eg. rootfolder/10_demo")
parser.add_argument("--instance_type", required=False, default="ml.g4dn.2xlarge", help="Instance type used for training, default is ml.g4dn.2xlarge")

args = parser.parse_args()
api_endpoint_url = args.api_url
api_key = args.api_key
creator = args.creator
model_s3_path = args.model_s3_path
folder_path = args.dataset_local_folder_path
s3_bucket_name = args.s3_bucket_name
s3_prefix = args.s3_prefix
instance_type = args.instance_type

ep = ApiEndpoint()
ep.api_endpoint_url = api_endpoint_url
ep.api_key = api_key


def upload_folder_to_s3(bucket_name, s3_prefix, folder_path):
    """
    Upload a folder with multiple files and subfolders to an S3 bucket
    """
    s3_client = boto3.client('s3')
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            local_file = os.path.join(root, file)
            s3_key = os.path.relpath(local_file, folder_path)

            try:
                s3_client.upload_file(local_file, bucket_name, os.path.join(s3_prefix, s3_key))
                print(f'Successfully uploaded {local_file} to {bucket_name}/{s3_prefix}/{s3_key}')
            except Exception as e:
                print(f'Error uploading {local_file}: {e}')

def create_training_job(api_endpoint_url, api_key, creator, model_s3_path, dataset_s3_path, instance_type="ml.g4dn.2xlarge"):
    """
    Create a Kohya training job
    """
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }
    body = {
        "lora_train_type": "kohya",
        "creator": creator,
        "params": {
            "training_params": {
                "training_instance_type": instance_type,
                "s3_model_path": model_s3_path,
                "s3_data_path": dataset_s3_path
            }
        }
    }

    response = requests.post(api_endpoint_url + '/trainings', headers=headers, data=json.dumps(body))

    print(f'Response status code: {response.status_code}')
    print(f'Response body: {response.json()}')

    return response.json()

def get_training_job(api_endpoint_url, api_key, job_id, creator):
    """
    Get a training job by job id
    """
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json',
        'creator': creator
    }

    response = requests.get(f"{api_endpoint_url}/trainings/{job_id}", headers=headers)

    print(f'Response status code: {response.status_code}')
    print(f'Response body: {response.json()}')

    return response.json()

def main():
    # Define the API endpoint and API key
    # api_endpoint = 'https://your-api-gateway-url'
    # api_key = 'your-api-key'
    MAX_RETRY = 60
    count = 0

    upload_folder_to_s3(s3_bucket_name, s3_prefix, folder_path)
    dataset_s3_path = f's3://{s3_bucket_name}/{s3_prefix}'

    create_training_job_response = create_training_job(ep.api_endpoint_url, ep.api_key, creator, model_s3_path, dataset_s3_path, instance_type)
    print(create_training_job_response)
    time.sleep(3)
    training_job_id = create_training_job_response['data']['id']
    print(f"Training job id: {training_job_id}")

    while count < MAX_RETRY:
        get_training_job_response = get_training_job(ep.api_endpoint_url, ep.api_key, training_job_id, creator)
        status = get_training_job_response["data"]["job_status"]
        #TODO: determine which status is expected
        if "Succeed" == status:
            print('Training job succeeded')
            break
        elif "Failed" == status:
            print('Training job failed, please check the SageMaker training logs in SageMaker console')
            break
        elif "Stopped" == status:
            print('Training job stopped, this could be stopped by manual operation')
            break
        else:
            # Initial
            print(f'Attempt: {count + 1}, training job is in {status} status, waiting for 60 seconds...')
            count += 1
            time.sleep(60)

if __name__ == "__main__":
    main()
