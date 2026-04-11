import json
import boto3
import os

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    try:
        short_id = event.get("pathParameters", {}).get("short_id", "").strip()

        if not short_id:
            return response(400, {"error": "Missing short ID"})

        result = table.get_item(Key={"short_id": short_id})
        item = result.get("Item")

        if not item:
            return response(404, {"error": "Short URL not found"})

        # Increment click count
        table.update_item(
            Key={"short_id": short_id},
            UpdateExpression="SET clicks = clicks + :inc",
            ExpressionAttributeValues={":inc": 1}
        )

        return {
            "statusCode": 301,
            "headers": {
                "Location": item["original_url"],
                "Access-Control-Allow-Origin": "*"
            },
            "body": ""
        }

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