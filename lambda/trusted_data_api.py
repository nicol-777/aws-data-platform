import json
import boto3
import pandas as pd
import io

s3 = boto3.client("s3")

BUCKET_NAME = "nicol-data-trust-project"

def lambda_handler(event, context):

    files = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix="trusted/"
    )

    if "Contents" not in files:
        return {
            "statusCode": 404,
            "body": json.dumps("No trusted data found")
        }

    latest_file = sorted(files["Contents"], key=lambda x: x["LastModified"], reverse=True)[0]["Key"]

    response = s3.get_object(
        Bucket=BUCKET_NAME,
        Key=latest_file
    )

    df = pd.read_csv(io.BytesIO(response["Body"].read()))

    data = df.head(10).to_dict(orient="records")

    return {
        "statusCode": 200,
        "body": json.dumps(data)
    }