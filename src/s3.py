import boto3
import os

class S3:
  
    def __init__(self, s3Config):

        self.s3Config = s3Config

        if not s3Config['endpoint_url']:

            raise ValueError('S3 endpoint_url is required')
        
        if not s3Config['aws_access_key_id']:

            raise ValueError('S3 aws_access_key_id is required')
        
        if not s3Config['aws_secret_access_key']:
            
            raise ValueError('S3 aws_secret_access_key is required')
        
        if not s3Config['bucket_name']:
                
            raise ValueError('S3 bucket_name is required')

        self.s3_resource = boto3.resource('s3',
        endpoint_url = s3Config['endpoint_url'],
        aws_access_key_id = s3Config['aws_access_key_id'],
        aws_secret_access_key = s3Config['aws_secret_access_key']
        )

        self.s3_bucket = self.s3_resource.Bucket(name=s3Config['bucket_name'])

    def testConnection(self):

        try:

            self.s3_bucket.creation_date

        except:

            raise ValueError('S3 connection failed')
        
    def uploadFile(self, filePath):
        name = os.path.basename(filePath)
        name = f"{self.s3Config['dir']}/{name}"
        self.s3_bucket.upload_file(
            Filename=filePath,
            Key=name
        )
        return