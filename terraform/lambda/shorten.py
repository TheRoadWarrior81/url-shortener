import json
import random
import string
import boto3
import os
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        original_url = body.get("url", "").strip()

        if not original_url:
            return response(400, {"error": "URL is required"})

        if not original_url.startswith(("http://", "https://")):
            return response(400, {"error": "URL must start with http:// or https://"})

        short_id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))

        table.put_item(Item={
            "short_id": short_id,
            "original_url": original_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "clicks": 0
        })

        domain = os.environ["DOMAIN"]
        return response(200, {
            "short_url": f"https://{domain}/{short_id}",
            "short_id": short_id
        })

    except Exception as e:
        return response(500, {"error": str(e)})


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }