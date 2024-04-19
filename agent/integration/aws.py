def pmpt_s3_credentials():
    return f"""
    The credentials for the S3 bucket are stored in the environment variables with the following names:
    
    - Access Key ID: 'AWS_ACCESS_KEY_ID'
    - Secret Access Key: AWS_SECRET_ACCESS_KEY'
    """
