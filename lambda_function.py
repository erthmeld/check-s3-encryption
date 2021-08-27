import json
import boto3
import botocore.exceptions


def lambda_handler(event, context):
    """Lambda function to identify unencrypted s3 buckets associated with the AWS
    account in use and send an email notification via an SNS resource.
    """

    checkS3 = check_s3()
    response = checkS3.send_unencrypted_alerts("arn:aws:sns:us-east-1:996921890895:gene-crumpler-s3-encryption")
    return response


class check_s3:
    """ Check s3 resources class
    
    Class object intantiates several boto3 client connections used to 
    interact with AWS service endpoints for the purpose of checking s3
    resources and notifying in the event an alert needs to be sent.
    
    Attr:
        __s3Client(object): boto3 AWS s3 client
        __snsClient(object): boto3 AWS SNS client
        __stsClient(object): boto3 AWS STS client
        __unencryptedBuckets(list): List of unencrypted buckets on which to alert
    """

    __s3Client = boto3.client('s3')
    __snsClient = boto3.client('sns')
    __stsClient = boto3.client('sts')
    __unencryptedBuckets = []

    def __init__(self):
        """ Class object initialization method
        
        Queries s3 via boto3 s3client connection to intantiate the buckets 
        object property. Also calls methods to set unencryptedBuckets, 
        alertMessage, and alertSubject properties.
        """
        self.__buckets = self.__s3Client.list_buckets()
        self.__set_unencrypted_buckets()
        self.set_unencrypted_alert_message(self.__unencryptedBuckets)


    def __set_unencrypted_buckets(self):
        for bucket in self.__buckets['Buckets']:
            if not self.__is_bucket_encryped(bucket['Name']):
                self.__unencryptedBuckets.append(bucket)


    def __is_bucket_encryped(self, bucketName):
        try:
            encryption = self.__s3Client.get_bucket_encryption(Bucket=bucketName)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                return False
            else:
                raise e
        else:
            return True


    def set_unencrypted_alert_message(self, buckets, **kwargs):
        accountId = self.__stsClient.get_caller_identity().get('Account')
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


    def send_unencrypted_alerts(self, *topicList):
        """ Sends alert subject and message defined by class method set_unencrypted_alert_message
        to any topics provided by *topicList param.
        
        Params:
            *topicList(list): List of TopicArn strings to publish to

        Returns:
            responses(dict[TopicArn:response]): Response json data from each sns publish call
            Or a string literal describing why it did not attempt to publish
            to an SNS topic

        """
        responses = {}
        if len(self.__unencryptedBuckets) > 0:
            if len(topicList) > 0:
                for topicARN in topicList:
                    responses[topicARN] = self.__snsClient.publish(
                        TopicArn=topicARN,
                        Subject=self.alertSubject,
                        Message=self.alertMessage)
            else:
                return "No SNS topics provided"
        else:
            return "No unencrypted buckets found"
        return responses
