import boto3
from datetime import datetime
import time


# AWS credentials (configure according to your AWS setup)
aws_access_key = '####'
aws_secret_key = '####'
aws_region = 'us-east-1'


# Define global variables
sqs = boto3.client('sqs', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=aws_region)
ec2 = boto3.client('ec2', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=aws_region)
s3 = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=aws_region)


request_sqs_queue_name = '####'

class InstanceManager:
    def __init__(self, ami_id, instance_type):
        self.ami_id = ami_id
        self.instance_type = instance_type
        self.instances = []

    def spawn_instance(self, ami_id, instance_type, instance_name, security_group_ids, key_name):
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=security_group_ids,
            KeyName=key_name,
            TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': instance_name
                    },
                ]
            },
        ]
        )
        instance_id = response['Instances'][0]['InstanceId']
        self.instances.append(instance_id)
        print(f"Created instance {instance_name} with id {instance_id}")

    def terminate_instance(self, instance_id):
        print('Deleting instace ', instance_id)
        ec2.terminate_instances(InstanceIds=[instance_id])

    def get_queue_size(self):
        response = sqs.get_queue_attributes(
            QueueUrl=request_sqs_queue_name,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        queue_size = int(response['Attributes']['ApproximateNumberOfMessages'])
        print(queue_size)
        if queue_size > 0:
            print('Current queue size',queue_size)
        return queue_size

    def scale_out(self):
        queue_size = self.get_queue_size()
        current_instance_count = len(self.instances)

        if current_instance_count >= queue_size or current_instance_count==20:
            return  # No need to spawn additional instances

        instances_to_spawn = min(queue_size - current_instance_count, 20)  # Maximum of 20 instances

        for _ in range(instances_to_spawn):
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            instance_name = f'app-tier-instance-{current_time}'
            self.spawn_instance(self.ami_id, self.instance_type, instance_name, ['sg-0a3c1bae415f1c7d1'], 'my_key_pair')


    def scale_in(self):

        if len(self.instances) == 0:
            print('No instances available. Exiting scale-in process.')
            return

        consecutive_checks = 0
        while self.get_queue_size() == 0 and len(self.instances) > 0:
            # Give some buffer time before executing delete
            print('Sleeping for 30 seconds before checking again...')
            time.sleep(30)  # Sleep for 1 minute
            consecutive_checks += 1

            if consecutive_checks >= 3:
                print('No messages in the queue after 3 consecutive checks. Terminating all instances.')
                for instance_id in self.instances:
                    self.terminate_instance(instance_id)
                self.instances = []  # Clear the list of instances
                break  # Exit the loop

        # if consecutive_checks < 3:
        #     print('Messages detected in the queue. Exiting scale-in process.')


    def manage_instances(self):
        while True:
            #print('Calling Scale out!!!')
            self.scale_out()
            # print('Calling Scale in!!!')
            self.scale_in()
            time.sleep(5)  # Adjust polling interval as needed


# Enable all the print statements for logging
if __name__ == "__main__":
    ami_id = 'ami-0c3b449ae7df7f82c'
    instance_type = 't2.micro'

    manager = InstanceManager(ami_id, instance_type)
    manager.manage_instances()

