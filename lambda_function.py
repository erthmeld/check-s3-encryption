import json
import boto3
import botocore.exceptions


def lambda_handler(event, context):
    """Lambda function to identify unencrypted s3 buckets associated with the AWS
    account in use and send an email notification via an SNS resource.
    """

    s3Client = boto3.client('s3')

    all_buckets = get_buckets(s3Client)
    unencrypted_buckets = []

    for bucket in all_buckets['Buckets']:
        if not is_bucket_encryped(s3Client, bucket['Name']):
            unencrypted_buckets.append(bucket)
    
    response = send_encryption_alert(unencrypted_buckets)
    return response

def get_buckets(client):
    """Queries s3 via boto3 client connection to generate and return a list of 
    s3 buckets associated with the current account/region.
    """
    
    s3Buckets = client.list_buckets()
    return s3Buckets

def is_bucket_encryped(client, bucketName):
    try:
        encryption = client.get_bucket_encryption(Bucket=bucketName)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
            return False
        else:
            raise e
    else:
        return True
        
def send_encryption_alert(buckets):
    topicARN = 'arn:aws:sns:us-east-1:996921890895:gene-crumpler-s3-encryption'
    accountId = boto3.client('sts').get_caller_identity().get('Account')

    subject= "ALERT:  Unencrypted s3 buckets found"
    message = "The s3 buckets specified below do not have a server side encryption configuration. \
    Please review and correct the configuration if required. \nAccount ID:" + accountId + "\n"
    for bucket in buckets:
        message = message + "\tBucket Name:  " + bucket['Name']
        
    snsResource = boto3.resource('sns')
    snsTopic = snsResource.Topic(topicARN)
    snsTopic.load()
    response = snsTopic.publish(
        Subject=subject,
        Message=message)
    return response