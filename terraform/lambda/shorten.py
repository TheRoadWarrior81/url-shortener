import json
import random
import string
import boto3
import os
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

MAX_RETRIES = 3

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        original_url = body.get("original_url", "").strip()

        # Validate presence
        if not original_url:
            return response(400, {"error": "URL is required"})

        # Validate scheme
        if not original_url.startswith(("http://", "https://")):
            return response(400, {"error": "URL must start with http:// or https://"})

        # Validate parseable URL with a real domain
        parsed = urlparse(original_url)
        if not parsed.netloc or "." not in parsed.netloc:
            return response(400, {"error": "Invalid URL — must include a valid domain"})

        # Generate unique short ID with collision check
        short_id = None
        for _ in range(MAX_RETRIES):
            candidate = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            result = table.get_item(Key={"short_id": candidate})
            if "Item" not in result:
                short_id = candidate
                break

        if not short_id:
            return response(500, {"error": "Could not generate a unique ID, please try again"})

        table.put_item(Item={
            "short_id": short_id,
            "original_url": original_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "clicks": 0
            "expires_at": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        })

        domain = os.environ["DOMAIN"]
        return response(200, {
            "short_url": f"https://{domain}/{short_id}",
            "short_id": short_id
        })

    except json.JSONDecodeError:
        return response(400, {"error": "Invalid request body"})
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
