# Cloud-Based-multi-tiered-Face-Recognition-System

This project focuses on developing an elastic face recognition application using the IaaS resources from AWS. The application is designed to utilize a multi-tier architecture to dynamically scale based on demand and perform face recognition using a machine learning model.

## Project Structure
Web Tier: Handles incoming image requests and sends them to the App Tier for processing. It also returns the recognition results to the users.
App Tier: Processes image recognition using a pre-trained deep learning model.
Data Tier: Manages data storage and retrieval from AWS S3 buckets.

## Technology Stack
AWS EC2
AWS S3
AWS SQS
Python
Deep Learning Models (PyTorch)
Setup Instructions

## Prerequisites
AWS Account
AWS CLI configured
Python 3.x
Access to AWS services (EC2, S3, SQS)
Deployment

## Clone the repository:
bash
Copy code
git clone https://github.com/your-github-username/elastic-face-recognition.git
cd elastic-face-recognition

## Configure AWS Credentials:
bash
Copy code
aws configure

## Launch the EC2 Instance:
Ensure the EC2 instance is running and has the appropriate IAM roles attached for accessing S3 and SQS.

## Setup S3 Buckets:
Create two S3 buckets for input and output as described in the project guidelines.

## Setup SQS Queues:
Create request and response queues in SQS to handle communication between web and app tiers.

## Deploy the Application:
Adjust the security group settings to allow traffic on port 8000.
Deploy the Python Flask app on the EC2 instance to handle HTTP requests.

## Usage:
Send a POST request to the deployed application with an image file. The application will return the face recognition result in plain text format.

## Example POST request using curl:

bash
Copy code
curl -X POST -F "inputFile=@path_to_image.jpg" http://ec2-instance-public-ip:8000/

Testing
Use the provided workload generator to simulate traffic and test the scalability and performance of the application.
Check the output in the designated S3 output bucket.
