import os
from flask import Flask, request
import boto3
from botocore.exceptions import NoCredentialsError
import subprocess
import time
from datetime import datetime
import sqlite3
import logging





app = Flask(__name__)

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

logging.basicConfig(filename='/home/ubuntu/cc_project/webtier.log', level=logging.INFO, format='%(asctime)s - %(message)s')


@app.route('/', methods=['POST'])
def process_image():
    if 'inputFile' in request.files:
        image_file = request.files['inputFile']
        logging.info('Received request for %s',image_file.filename)

        

        conn = sqlite3.connect('ImageClassification.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classification_output (
                image_name TEXT,
                name TEXT
            )
        ''')
        conn.commit()
        cursor.execute('DELETE FROM classification_output')
        conn.commit()


        # try to upload to S#
        temp_file_path = f'/home/ubuntu/cc_project/face_images_1000/{image_file.filename}'
        image_file.save(temp_file_path)

        # upload_to_s3(temp_file_path, input_s3_bucket_name)
        logging.info(f"Uploaded {temp_file_path} to {input_s3_bucket_name}")                

        # Send message to request SQS queue
        send_message_to_sqs(os.path.basename(temp_file_path), input_s3_bucket_name)
        logging.info(f"Copied to request SQS:  s3://{input_s3_bucket_name}/{temp_file_path}")  


        # # consume messages from the output SQS and stores it in DB
        img_name = image_file.filename.split('.')[0]
        while True:
            logging.info('Waiting for the image %s', img_name)
            cursor.execute("SELECT name FROM classification_output WHERE image_name = ?", (img_name,))
            result = cursor.fetchone()
            if result:
                name_field = result[0]
                logging.info(f"Result found for {img_name} = {name_field}. Hence taking it and deleting it from DB")  
                cursor.execute("DELETE FROM classification_output WHERE image_name = ?", (img_name,))
                conn.commit()
                conn.close()
                return img_name+':'+name_field
            else:
                time.sleep(0.5)


def upload_to_s3(file_path, bucket_name):
    try:
        s3.upload_file(file_path, bucket_name, os.path.basename(file_path))
        return f'File uploaded to S3: {os.path.basename(file_path)}'
    except Exception as e:
        return f'Error uploading to S3: {e}'

def send_message_to_sqs(file_name, bucket_name):
    # Send message to request SQS queue with S3 file location path
    s3_path = f's3://{bucket_name}/{file_name}'
    sqs.send_message(
        QueueUrl=request_sqs_queue_url,
        MessageBody=s3_path,
        MessageAttributes={
            'FileName': {
                'DataType': 'String',
                'StringValue': file_name
            },
            'BucketName': {
                'DataType': 'String',
                'StringValue': bucket_name
            }
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)