import json
import os
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    short_id = (event.get("pathParameters") or {}).get("short_id", "")

    if not short_id:
        return {
            "statusCode": 400,
            "headers": cors_headers(),
            "body": json.dumps({"message": "short_id is required"}),
        }

    response = table.get_item(Key={"short_id": short_id})
    item = response.get("Item")

    if not item:
        return {
            "statusCode": 404,
            "headers": cors_headers(),
            "body": json.dumps({"message": "Short URL not found"}),
        }

    return {
        "statusCode": 200,
        "headers": cors_headers(),
        "body": json.dumps({
            "short_id": item["short_id"],
            "original_url": item["original_url"],
            "click_count": int(item.get("click_count", 0)),
        }),
    }

def cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
    }