import boto3
import botocore.exceptions


def lambda_handler(event, context):
    """Lambda function to identify unencrypted s3 buckets associated with the AWS
    account in use and send an email notification via an SNS resource.

    Returns:
        response(dict): SNS topic ARN as key and publish reponse as value
    """

    checkS3 = check_s3()
    response = checkS3.send_unencrypted_alerts("arn:aws:sns:us-east-1:996921890895:gene-crumpler-s3-encryption")
    return response


class check_s3:
    """ Check s3 resources class
    
    Object of class intantiates several boto3 client connections used to 
    interact with AWS service endpoints for the purpose of checking S3
    resources and sending a notification via SNS in the event of an alert.
    
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
        """ Private method to set the unencrypted_buckets property. """

        for bucket in self.__buckets['Buckets']:
            if not self.__is_bucket_encryped(bucket['Name']):
                self.__unencryptedBuckets.append(bucket)


    def __is_bucket_encryped(self, bucketName):
        """ Private method to check if a bucket has a server side 
        encryption configuration 

        Params:
            bucketName(string): S3 bucket name to query

        Returns:
            bool literal of True if there is no exception caught with the 
            error code 'ServerSideEncryptionConfigurationNotFoundError', and False 
            otherwise.

        Raises:
            botocore ClientError exception if one is caught and it does not match 
            the error code specified above.
        """

        # Since there is no s3 property/metadata  for encryption you must check 
        # and catch a specific exception to verify if it's setup
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
        """ Public method to set the class object's alertSubject and 
        alertMessage properties. 
        
        If no kwargs params are passed in, then we use the default subject and 
        message strings in this method. Otherwise we set the object's properties 
        accordingly.

        Params:
            buckets(list): Names of unencrypted buckets found on S3
        """

        accountId = self.__stsClient.get_caller_identity().get('Account')
        
        if 'subject' in kwargs:
            self.alertSubject = kwargs['subject']
        else:
            self.alertSubject = "ALERT:  Unencrypted s3 buckets found"
        
        if 'message' in kwargs:
                self.alertSubject = kwargs['subject']
        else:
            self.alertMessage = "The s3 buckets specified below do not have a server side encryption configuration. \
Please review and correct the configuration if required."

        # Append Account ID to object's alertMessage property
        self.alertMessage = self.alertMessage + "\n\nAccount ID:  " + accountId + ""
        
        # Append unencrypted bucket names passed in via buckets parameter to 
        # object's alertMessage property
        for bucket in buckets:
            self.alertMessage = self.alertMessage + "\n\tBucket Name:  " + bucket['Name']


    def send_unencrypted_alerts(self, *topicList):
        """ Sends alert subject and message defined by class method set_unencrypted_alert_message
        to any topics provided by *topicList param.
        
        Params:
            *topicList(*args): Topic ARN strings to publish to

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
