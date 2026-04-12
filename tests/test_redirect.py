"""
Unit tests for redirect.py Lambda function.

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


def _seed_item(table, short_id="abc123", original_url="https://www.example.com", clicks=0):
    """Insert a pre-existing short URL into the mock table."""
    table.put_item(Item={
        "short_id": short_id,
        "original_url": original_url,
        "created_at": "2024-01-01T00:00:00+00:00",
        "clicks": clicks,
        "expires_at": 9999999999,
    })


def _make_event(short_id: str | None = "abc123") -> dict:
    """Build a minimal API Gateway HTTP v2 event for redirect."""
    if short_id is None:
        return {"pathParameters": {}}
    return {"pathParameters": {"short_id": short_id}}


@mock_aws
class TestRedirectLambda(unittest.TestCase):

    def setUp(self):
        os.environ["TABLE_NAME"] = TABLE_NAME
        os.environ["AWS_DEFAULT_REGION"] = "ca-central-1"
        os.environ["AWS_ACCESS_KEY_ID"] = "test"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

        self.dynamodb = boto3.resource("dynamodb", region_name="ca-central-1")
        self.table = _make_table(self.dynamodb)

        if "redirect" in sys.modules:
            del sys.modules["redirect"]

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "terraform", "lambda"))
        import redirect as redirect_module
        self.handler = redirect_module.lambda_handler

    def tearDown(self):
        self.table.delete()
        sys.path.pop(0)

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_valid_short_id_returns_302(self):
        """A known short_id returns a 302 redirect."""
        _seed_item(self.table)
        result = self.handler(_make_event("abc123"), {})
        self.assertEqual(result["statusCode"], 302)

    def test_redirect_location_header_is_original_url(self):
        """The Location header points to the original URL."""
        _seed_item(self.table, short_id="abc123", original_url="https://www.example.com/long-path")
        result = self.handler(_make_event("abc123"), {})
        self.assertEqual(result["headers"]["Location"], "https://www.example.com/long-path")

    def test_redirect_increments_click_count(self):
        """Each redirect increments the clicks counter by exactly 1."""
        _seed_item(self.table, short_id="abc123", clicks=5)
        self.handler(_make_event("abc123"), {})
        item = self.table.get_item(Key={"short_id": "abc123"}).get("Item")
        self.assertEqual(int(item["clicks"]), 6)

    def test_multiple_redirects_accumulate_clicks(self):
        """Three consecutive redirects increment clicks from 0 to 3."""
        _seed_item(self.table, short_id="abc123", clicks=0)
        for _ in range(3):
            self.handler(_make_event("abc123"), {})
        item = self.table.get_item(Key={"short_id": "abc123"}).get("Item")
        self.assertEqual(int(item["clicks"]), 3)

    def test_cors_header_present_on_redirect(self):
        """CORS header is present on 301 responses."""
        _seed_item(self.table)
        result = self.handler(_make_event("abc123"), {})
        self.assertEqual(result["headers"]["Access-Control-Allow-Origin"], "*")

    # ------------------------------------------------------------------
    # Not found
    # ------------------------------------------------------------------

    def test_unknown_short_id_returns_404(self):
        """A short_id that doesn't exist in DynamoDB returns 404."""
        result = self.handler(_make_event("xxxxxx"), {})
        self.assertEqual(result["statusCode"], 404)
        body = json.loads(result["body"])
        self.assertIn("message", body)

    def test_404_does_not_increment_clicks(self):
        """A failed lookup for a missing ID doesn't affect other items."""
        _seed_item(self.table, short_id="abc123", clicks=2)
        self.handler(_make_event("xxxxxx"), {})  # unknown ID
        item = self.table.get_item(Key={"short_id": "abc123"}).get("Item")
        self.assertEqual(int(item["clicks"]), 2)

    # ------------------------------------------------------------------
    # Missing / empty short_id
    # ------------------------------------------------------------------

    def test_missing_short_id_returns_400(self):
        """An event with no short_id path parameter returns 400."""
        result = self.handler(_make_event(None), {})
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)

    def test_empty_short_id_returns_400(self):
        """An empty string short_id (after strip) returns 400."""
        result = self.handler(_make_event("   "), {})
        self.assertEqual(result["statusCode"], 400)

    def test_missing_path_parameters_key_returns_400(self):
        """An event with no pathParameters key at all is handled gracefully."""
        result = self.handler({}, {})
        self.assertEqual(result["statusCode"], 400)

    # ------------------------------------------------------------------
    # Response body
    # ------------------------------------------------------------------

    def test_redirect_body_is_empty_string(self):
        """301 response body is an empty string (browsers ignore it anyway)."""
        _seed_item(self.table)
        result = self.handler(_make_event("abc123"), {})
        self.assertEqual(result["body"], "")

    def test_cors_header_present_on_404(self):
        """CORS header is present on error responses."""
        result = self.handler(_make_event("xxxxxx"), {})
        self.assertEqual(result["headers"]["Access-Control-Allow-Origin"], "*")


if __name__ == "__main__":
    unittest.main()
