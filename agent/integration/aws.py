import os
import questionary


def pmpt_s3_credentials():
    return f"""
    The credentials for the S3 bucket are stored in the environment variables with the following names:
    
    - Access Key ID: 'AWS_ACCESS_KEY_ID'
    - Secret Access Key: AWS_SECRET_ACCESS_KEY'
    """


def aws_credentials():
    """
    Prompt the user for the AWS credentials and set to the environment variables.
    :return: the AWS Access Key ID and the AWS Secret Access Key.
    """
    aws_access_key_id = questionary.text("Enter the AWS Access Key ID:").ask()
    aws_secret_access_key = questionary.text("Enter the AWS Secret Access Key:").ask()

    os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
    return aws_access_key_id, aws_secret_access_key
