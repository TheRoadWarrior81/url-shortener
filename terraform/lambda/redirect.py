import json
import boto3
import os
import traceback

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):
    try:
        short_id = event.get("pathParameters", {}).get("short_id", "").strip()

        if not short_id:
            return response(400, {"message": "Missing short ID"})

        result = table.get_item(Key={"short_id": short_id})
        item = result.get("Item")

        if not item:
            return response(404, {"message": "Short URL not found"})

        # Increment click count
        table.update_item(
            Key={"short_id": short_id},
            UpdateExpression="SET clicks = if_not_exists(clicks, :zero) + :inc",
            ExpressionAttributeValues={":inc": 1, ":zero": 0}
        )

        return {
            "statusCode": 302,
            "headers": {
                "Location": item["original_url"],
                "Access-Control-Allow-Origin": "*"
            },
            "body": ""
        }

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
