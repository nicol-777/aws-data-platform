import json
import boto3
import pandas as pd
import io
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

BUCKET_NAME = "nicol-data-trust-project"
SNS_TOPIC_ARN = "arn:aws:sns:eu-north-1:768286546133:data-validation-alerts"
TABLE_NAME = "data-validation-logs"

def lambda_handler(event, context):
    
    table = dynamodb.Table(TABLE_NAME)
    file_key = event['Records'][0]['s3']['object']['key']
    timestamp = datetime.now().isoformat()
    
    response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
    content = response['Body'].read()
    
    df = pd.read_csv(io.BytesIO(content))
    
    issues = []
    
    if (df["value"] < 0).any():
        issues.append("Negative values found")
        
    df["last_updated"] = pd.to_datetime(df["last_updated"])
    
    if (datetime.now() - df["last_updated"]).dt.days.max() > 30:
        issues.append("Outdated data found")
    
    if issues:
        destination = "quarantine"
        s3.put_object(Bucket=BUCKET_NAME,
                      Key="quarantine/" + file_key.split("/")[-1],
                      Body=content)
        
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message="Data validation failed: " + str(issues)
        )
        
    else:
        destination = "trusted"
        s3.put_object(Bucket=BUCKET_NAME,
                      Key="trusted/" + file_key.split("/")[-1],
                      Body=content)
    
    # Log to DynamoDB
    table.put_item(Item={
        "file_name": file_key.split("/")[-1],
        "timestamp": timestamp,
        "result": "FAILED" if issues else "PASSED",
        "issues": str(issues) if issues else "None",
        "destination": destination
    })
    
    return {
        'statusCode': 200,
        'body': json.dumps('Validation complete')
    }