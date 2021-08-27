import json
import boto3
import botocore.exceptions


def lambda_handler(event, context):
    """Lambda function to identify unencrypted s3 buckets associated with the AWS
    account in use and send an email notification via an SNS resource.
    """

    checkS3 = check_s3()
    response = checkS3.send_unencrypted_alerts("")
    return response


class check_s3:
    s3Client = boto3.client('s3')
    snsClient = boto3.client('sns')
    stsClient = boto3.client('sts')
    unencryptedBuckets = []

    def __init__(self):
        self.buckets = self.s3Client.list_buckets()
        self.__set_unencrypted_buckets()
        self.set_unencrypted_alert_message(self.unencryptedBuckets)

    def __get_buckets(self):
        """Queries s3 via boto3 client connection to generate and return a list of 
        s3 buckets associated with the current account/region.
        """
        
        return self.buckets

    def __set_unencrypted_buckets(self):
        for bucket in self.buckets['Buckets']:
            if not self.__is_bucket_encryped(bucket['Name']):
                self.unencryptedBuckets.append(bucket)

    def __is_bucket_encryped(self, bucketName):
        try:
            encryption = self.s3Client.get_bucket_encryption(Bucket=bucketName)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                return False
            else:
                raise e
        else:
            return True

    def set_unencrypted_alert_message(self, buckets, **kwargs):
        accountId = self.stsClient.get_caller_identity().get('Account')
        if 'subject' in kwargs:
            self.alertSubject = kwargs['subject']
        else:
            self.alertSubject = "ALERT:  Unencrypted s3 buckets found"
        if 'message' in kwargs:
                self.alertSubject = kwargs['subject']
        else:
            self.alertMessage = "The s3 buckets specified below do not have a server side encryption configuration. \
Please review and correct the configuration if required. \n\nAccount ID:  " + accountId + "\n"
        
        for bucket in buckets:
            self.alertMessage = self.alertMessage + "\tBucket Name:  " + bucket['Name']

    def send_unencrypted_alerts(self, topicList):
        if len(self.unencryptedBuckets) > 0:
            topicARN = 'arn:aws:sns:us-east-1:996921890895:gene-crumpler-s3-encryption'
            response = self.snsClient.publish(
                TopicArn=topicARN,
                Subject=self.alertSubject,
                Message=self.alertMessage)
            return response
        else:
            return "No unencrypted buckets found"