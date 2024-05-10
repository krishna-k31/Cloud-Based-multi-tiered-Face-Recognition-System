import os
from flask import Flask, request
import boto3
from botocore.exceptions import NoCredentialsError
import subprocess
import time
from datetime import datetime
import sqlite3
import logging


logging.basicConfig(filename='/home/ubuntu/cc_project/response_q_consume.log', level=logging.INFO, format='%(asctime)s - %(message)s')


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


def get_queue_size():
        response = sqs.get_queue_attributes(
            QueueUrl=request_sqs_queue_name,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        queue_size = int(response['Attributes']['ApproximateNumberOfMessages'])
        if queue_size > 0:
            logging.info('Queue size',queue_size)
        return queue_size


def consume_messages_output_sqs():
    # Retrieve messages from output SQS queue
    while True:
        response = sqs.receive_message(
            QueueUrl=result_sqs_queue_url,
            MaxNumberOfMessages=10,  # Adjust as needed
            WaitTimeSeconds=20  # Adjust as needed
        )
        # Check if messages are received
        if 'Messages' in response:
            logging.info('response received')

            for message in response['Messages']:
                sqs.delete_message(
                    QueueUrl=result_sqs_queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                message_body = message['Body']
                logging.info('Deleted message from the queue: %s', message_body)
                img_name_sqs =  message_body.split(":")[0]
                name_sqs =  message_body.split(":")[1]
                conn = sqlite3.connect('ImageClassification.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO classification_output (image_name, name) VALUES (?, ?)", (img_name_sqs, name_sqs))
                conn.commit()
                conn.close()
                logging.info(f"Message written to db {img_name_sqs}:{name_sqs}")                

        # if get_queue_size() == 0:
        #     time.sleep(120)
            
consume_messages_output_sqs()