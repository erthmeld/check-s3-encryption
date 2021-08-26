import json
import boto3
import botocore.exceptions

def lambda_handler(event, context):
    """Lambda function to identify unencrypted s3 buckets associated with the AWS
    account in use and send an email notification via an SNS resource.
    """
    s3Client = boto3.client('s3')

    all_buckets = get_buckets(s3Client)
    unencrypted_buckets = {}

    for bucket in all_buckets['Buckets']:
        if not is_bucket_encryped(s3Client, bucket['Name']):
            print('Bucket not encrypted:  ' + bucket)
    
    #publish_sns("testing123", )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

def get_buckets(client):
    """Queries s3 via boto3 client connection to generate and return a list of 
    s3 buckets associated with the current account/region.
    """
    
    s3Buckets = client.list_buckets()
    return s3Buckets

def is_bucket_encryped(client, bucketName):
    try:
        encryption = client.get_bucket_encryption(Bucket=bucketName)
    except client.exceptions.ClientErr as e:
        if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
            return False
        else:
            raise e
    else:
        print(encryption)
        return True
        
def publish_sns(message):
    topicARN = 'arn:aws:sns:us-east-1:996921890895:gene-crumpler-s3-encryption'
    snsResource = boto3.resource('sns')
    topicsList = snsResource.topics.all()
    for topic in topicsList:
        print(topic.arn)
    snsTopic = snsResource.Topic('arn:aws:sns:us-east-1:996921890895:gene-crumpler-s3-encryption')
    snsTopic.load()
    response = snsTopic.publish(Message=message)
    print(response)