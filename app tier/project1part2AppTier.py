import boto3
from botocore.exceptions import NoCredentialsError
import subprocess
import time
import logging



logging.basicConfig(filename='/home/ubuntu/consume_and_process_messages.log', level=logging.INFO, format='%(asctime)s - %(message)s')



# AWS credentials (configure according to your AWS setup)
aws_access_key = '####'
aws_secret_key = '####'
aws_region = 'us-east-1'


# S3 buckets
input_s3_bucket_name = '####'
output_s3_bucket_name = '####'

# SQS queues
request_sqs_queue_name = '####'
result_sqs_queue_name = '####'

sqs = boto3.client('sqs', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=aws_region)
s3 = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=aws_region)



request_sqs_queue_url = sqs.get_queue_url(QueueName=request_sqs_queue_name)['QueueUrl']
result_sqs_queue_url = sqs.get_queue_url(QueueName=result_sqs_queue_name)['QueueUrl']



def consume_and_process_messages():

    polling_interval = 2  # Adjust as needed
    while True:
        try:
            # Receive messages from input SQS queue
            response = sqs.receive_message(
                QueueUrl=request_sqs_queue_url,
                MaxNumberOfMessages=1,  # Adjust as needed
                WaitTimeSeconds=20  # Adjust as needed
            )

            # Check if messages are received
            if 'Messages' in response:
                for message in response['Messages']:
                    logging.info('Message received:',message)
                    logging.info('Deleting this message')
                    # Delete the message from the queue
                    sqs.delete_message(
                        QueueUrl=request_sqs_queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    # Process the message (e.g., get image file from S3)
                    process_message(message)
            else:
                logging.info('No messages received')
        except Exception as e:
            logging.info(f'Error: {e}')
        time.sleep(polling_interval)


def process_message(message):
    # Extract message attributes (e.g., S3 object key)
    message_body = message['Body']
    # Fetch image from S3
    image_key = message_body.split("/")[-1]
    filename = image_key.split('/')[-1]
    image_file_path = fetch_image_from_s3(image_key)
    # Run face recognition script
    #image_file_path = f'/home/ubuntu/imagesDump/{filename}'
    logging.info('Running the face recog scrit for:'+filename)
    result = run_face_recognition(image_file_path)
    logging.info(f"Obtained the results for {filename} is {result}")
    # Store output in S3
    image_name = image_key.split('.')[0]
    store_output_in_s3(image_name, result)
    # Write result to output SQS queue
    write_to_output_queue(f'{image_name}:{result}')


def fetch_image_from_s3(image_key):
    filename = image_key.split('/')[-1]
    local_image_file_path = f'/home/ubuntu/imagesDump/{filename}'
    s3.download_file(input_s3_bucket_name, image_key, local_image_file_path)
    return local_image_file_path

def run_face_recognition(image_file_path):
    result = subprocess.run(['python3', '/home/ubuntu/face_recognition.py', image_file_path], capture_output=True)
    return result.stdout.decode().strip() 

def store_output_in_s3(image_name, classification_result):
    s3.put_object(Bucket=output_s3_bucket_name, Key=image_name, Body=classification_result)

def write_to_output_queue(result):
    # Write result to output SQS queue
    logging.info(f'write_to_output_queue result: {result}')
    sqs.send_message(QueueUrl=result_sqs_queue_name, MessageBody=result)
    logging.info(f'Done writing: {result}')



consume_and_process_messages()
