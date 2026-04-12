import json
import random
import string
import boto3
import os
import traceback
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

MAX_RETRIES = 3

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        if not isinstance(body, dict):
            return response(400, {"message": "Request body must be a JSON object"})

        original_url = body.get("original_url", "").strip()

        # Validate presence
        if not original_url:
            return response(400, {"message": "URL is required"})

        # Validate scheme
        if not original_url.startswith(("http://", "https://")):
            return response(400, {"message": "URL must start with http:// or https://"})

        # Validate parseable URL with a real domain
        parsed = urlparse(original_url)
        if not parsed.netloc or "." not in parsed.netloc:
            return response(400, {"message": "Invalid URL — must include a valid domain"})

        # Generate unique short ID with collision check
        short_id = None
        for _ in range(MAX_RETRIES):
            candidate = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            result = table.get_item(Key={"short_id": candidate})
            if "Item" not in result:
                short_id = candidate
                break

        if not short_id:
            return response(500, {"message": "Could not generate a unique ID, please try again"})

        table.put_item(Item={
            "short_id": short_id,
            "original_url": original_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "clicks": 0,
            "expires_at": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        })

        domain = os.environ["DOMAIN"]
        return response(200, {
            "short_url": f"https://{domain}/r/{short_id}",
            "short_id": short_id
        })

    except json.JSONDecodeError:
        return response(400, {"message": "Invalid request body"})
    except Exception as e:
        print(traceback.format_exc())
        return response(500, {"message": "Internal server error"})


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }
