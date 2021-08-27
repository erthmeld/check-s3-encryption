# Check S3 Encryption

Check S3 Encryption is a Python AWS Lambda function for checking whether 
default encryption is disabled on accessible S3 buckets.

## Installation

You can deploy the code manually via AWS Lambda web UI or as a directory 
or archive via the AWS SAM CLI. The only required code for functionality 
is contained in lamda_function.py file.

You will need to ensure that your Lamnda execution role has permission
policies for access to the appropriate S3 and SNS resources. 

## Usage

The Lambda can be triggered manually or in an automated fashion and will 
query any public S3 buckets associated with the account/region in which 
the Lambda was created/triggered.

See docstring for details on return data.
