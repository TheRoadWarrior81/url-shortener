"""
Unit tests for stats.py Lambda function.

Uses moto to mock DynamoDB — no real AWS calls are made.
Run with: python -m pytest tests/ -v
"""

import json
import os
import sys
import unittest

import boto3
from moto import mock_aws

TABLE_NAME = "url-shortener-urls"


def _make_table(dynamodb):
    return dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{"AttributeName": "short_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "short_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def _seed_item(table, short_id="abc123", original_url="https://www.example.com", clicks=42):
    table.put_item(Item={
        "short_id": short_id,
        "original_url": original_url,
        "created_at": "2024-01-01T00:00:00+00:00",
        "clicks": clicks,
        "expires_at": 9999999999,
    })


def _make_event(short_id: str | None = "abc123") -> dict:
    if short_id is None:
        return {"pathParameters": {}}
    return {"pathParameters": {"short_id": short_id}}


@mock_aws
class TestStatsLambda(unittest.TestCase):

    def setUp(self):
        os.environ["TABLE_NAME"] = TABLE_NAME
        os.environ["AWS_DEFAULT_REGION"] = "ca-central-1"
        os.environ["AWS_ACCESS_KEY_ID"] = "test"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

        self.dynamodb = boto3.resource("dynamodb", region_name="ca-central-1")
        self.table = _make_table(self.dynamodb)

        if "stats" in sys.modules:
            del sys.modules["stats"]

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "terraform", "lambda"))
        import stats as stats_module
        self.handler = stats_module.lambda_handler

    def tearDown(self):
        self.table.delete()
        sys.path.pop(0)

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_valid_short_id_returns_200(self):
        """A known short_id returns 200."""
        _seed_item(self.table)
        result = self.handler(_make_event("abc123"), {})
        self.assertEqual(result["statusCode"], 200)

    def test_response_body_contains_all_fields(self):
        """Response body includes short_id, original_url, and clicks."""
        _seed_item(self.table, short_id="abc123", original_url="https://www.example.com", clicks=7)
        result = self.handler(_make_event("abc123"), {})
        body = json.loads(result["body"])
        self.assertEqual(body["short_id"], "abc123")
        self.assertEqual(body["original_url"], "https://www.example.com")
        self.assertEqual(body["clicks"], 7)

    def test_response_body_uses_clicks_field_name(self):
        """Response body uses clicks key (not click_count) as API contract."""
        _seed_item(self.table, clicks=7)
        result = self.handler(_make_event("abc123"), {})
        body = json.loads(result["body"])
        self.assertIn("clicks", body)
        self.assertNotIn("click_count", body)

    def test_clicks_is_integer_not_decimal(self):
        """
        DynamoDB returns Decimal for numbers; the handler must convert to int.
        This verifies the int() cast is applied before JSON serialisation.
        """
        _seed_item(self.table, clicks=99)
        result = self.handler(_make_event("abc123"), {})
        body = json.loads(result["body"])
        self.assertIsInstance(body["clicks"], int)
        self.assertEqual(body["clicks"], 99)

    def test_zero_clicks_returned_correctly(self):
        """A brand-new URL with 0 clicks is returned as 0, not missing."""
        _seed_item(self.table, clicks=0)
        result = self.handler(_make_event("abc123"), {})
        body = json.loads(result["body"])
        self.assertEqual(body["clicks"], 0)

    def test_stats_does_not_modify_clicks(self):
        """Fetching stats must NOT increment the click counter."""
        _seed_item(self.table, clicks=3)
        self.handler(_make_event("abc123"), {})
        self.handler(_make_event("abc123"), {})
        item = self.table.get_item(Key={"short_id": "abc123"}).get("Item")
        self.assertEqual(int(item["clicks"]), 3)

    # ------------------------------------------------------------------
    # Not found
    # ------------------------------------------------------------------

    def test_unknown_short_id_returns_404(self):
        """A short_id not in DynamoDB returns 404."""
        result = self.handler(_make_event("xxxxxx"), {})
        self.assertEqual(result["statusCode"], 404)

    def test_404_body_contains_message_key(self):
        """stats.py uses 'message' (not 'error') in its 404 body."""
        result = self.handler(_make_event("xxxxxx"), {})
        body = json.loads(result["body"])
        self.assertIn("message", body)

    # ------------------------------------------------------------------
    # Missing / empty short_id
    # ------------------------------------------------------------------

    def test_missing_short_id_returns_400(self):
        """An event with no short_id path parameter returns 400."""
        result = self.handler(_make_event(None), {})
        self.assertEqual(result["statusCode"], 400)

    def test_none_path_parameters_returns_400(self):
        """pathParameters being None (not missing) is handled safely."""
        result = self.handler({"pathParameters": None}, {})
        self.assertEqual(result["statusCode"], 400)

    def test_missing_path_parameters_key_returns_400(self):
        """Event with no pathParameters key at all is handled gracefully."""
        result = self.handler({}, {})
        self.assertEqual(result["statusCode"], 400)

    # ------------------------------------------------------------------
    # Response shape
    # ------------------------------------------------------------------

    def test_cors_header_present_on_success(self):
        """CORS header is set on 200 responses."""
        _seed_item(self.table)
        result = self.handler(_make_event("abc123"), {})
        self.assertEqual(result["headers"]["Access-Control-Allow-Origin"], "*")

    def test_cors_header_present_on_404(self):
        """CORS header is set on 404 responses."""
        result = self.handler(_make_event("xxxxxx"), {})
        self.assertEqual(result["headers"]["Access-Control-Allow-Origin"], "*")

    def test_cors_header_present_on_400(self):
        """CORS header is set on 400 responses."""
        result = self.handler(_make_event(None), {})
        self.assertEqual(result["headers"]["Access-Control-Allow-Origin"], "*")


if __name__ == "__main__":
    unittest.main()
