import json
import boto3

def lambda_handler(event, context):
    # Retrieve the list of existing buckets
    get_buckets()
        
    publish_sns("testing123")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

def get_buckets():
    s3Client = boto3.client('s3')
    s3Buckets = s3Client.list_buckets()
    # Output the bucket names
    print('Existing buckets:')
    for bucket in s3Buckets['Buckets']:
        print(f'  {bucket["Name"]}')
        
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