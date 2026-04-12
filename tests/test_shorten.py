"""
Unit tests for shorten.py Lambda function.

Uses moto to mock DynamoDB — no real AWS calls are made.
Run with: python -m pytest tests/ -v
"""

import json
import os
import sys
import unittest
from unittest.mock import patch
from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

# ---------------------------------------------------------------------------
# Test infrastructure helpers
# ---------------------------------------------------------------------------

TABLE_NAME = "url-shortener-urls"
DOMAIN = "short.example.com"

def _make_table(dynamodb):
    """Create a local mock DynamoDB table matching the real schema."""
    return dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{"AttributeName": "short_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "short_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


def _make_event(body: dict | None = None, raw_body: str | None = None) -> dict:
    """Build a minimal API Gateway HTTP v2 event for shorten."""
    if raw_body is not None:
        serialized = raw_body
    else:
        serialized = json.dumps(body) if body is not None else "{}"
    return {"body": serialized}


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@mock_aws
class TestShortenLambda(unittest.TestCase):
    """All tests run inside a single @mock_aws decorator applied at class level."""

    def setUp(self):
        """
        Spin up a fresh mock DynamoDB table and import the handler.

        The handler module is imported *inside* the mock context so that
        the module-level `boto3.resource()` call hits the mock, not real AWS.
        """
        os.environ["TABLE_NAME"] = TABLE_NAME
        os.environ["DOMAIN"] = DOMAIN
        os.environ["AWS_DEFAULT_REGION"] = "ca-central-1"
        os.environ["AWS_ACCESS_KEY_ID"] = "test"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

        self.dynamodb = boto3.resource("dynamodb", region_name="ca-central-1")
        self.table = _make_table(self.dynamodb)

        # Force a clean import of the handler on every test so it picks up
        # the fresh mock table (avoids cross-test state via module cache).
        if "lambda.shorten" in sys.modules:
            del sys.modules["lambda.shorten"]
        if "shorten" in sys.modules:
            del sys.modules["shorten"]

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "terraform", "lambda"))
        import shorten as shorten_module
        self.handler = shorten_module.lambda_handler

    def tearDown(self):
        self.table.delete()
        sys.path.pop(0)

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_happy_path_returns_200_with_short_url(self):
        """A valid URL is shortened and stored in DynamoDB."""
        event = _make_event({"original_url": "https://www.example.com"})
        result = self.handler(event, {})

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertIn("short_url", body)
        self.assertIn("short_id", body)
        self.assertTrue(body["short_url"].startswith(f"https://{DOMAIN}/"))

    def test_happy_path_item_persisted_in_dynamodb(self):
        """The DynamoDB item written by shorten has all expected fields."""
        event = _make_event({"original_url": "https://www.example.com/path?q=1"})
        result = self.handler(event, {})

        body = json.loads(result["body"])
        short_id = body["short_id"]

        item = self.table.get_item(Key={"short_id": short_id}).get("Item")
        self.assertIsNotNone(item, "Item should exist in DynamoDB after shortening")
        self.assertEqual(item["original_url"], "https://www.example.com/path?q=1")
        self.assertEqual(int(item["clicks"]), 0)
        self.assertIn("created_at", item)
        self.assertIn("expires_at", item)

    def test_happy_path_http_url_accepted(self):
        """http:// (not just https://) URLs are valid inputs."""
        event = _make_event({"original_url": "http://insecure.example.com"})
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 200)

    def test_short_id_is_six_characters_alphanumeric(self):
        """Generated short_id is exactly 6 alphanumeric characters."""
        event = _make_event({"original_url": "https://www.example.com"})
        result = self.handler(event, {})

        body = json.loads(result["body"])
        short_id = body["short_id"]
        self.assertEqual(len(short_id), 6)
        self.assertTrue(short_id.isalnum())

    def test_url_with_whitespace_is_stripped(self):
        """Leading/trailing whitespace around the URL is ignored."""
        event = _make_event({"original_url": "  https://www.example.com  "})
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 200)

    # ------------------------------------------------------------------
    # Validation — empty / missing body
    # ------------------------------------------------------------------

    def test_empty_body_returns_400(self):
        """A completely empty body string is handled gracefully."""
        event = {"body": "{}"}
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("error", body)

    def test_missing_body_key_returns_400(self):
        """An event with no 'body' key at all is handled without crashing."""
        result = self.handler({}, {})
        self.assertEqual(result["statusCode"], 400)

    def test_empty_url_string_returns_400(self):
        """original_url present but empty string → 400."""
        event = _make_event({"original_url": ""})
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["error"], "URL is required")

    def test_whitespace_only_url_returns_400(self):
        """original_url that is only whitespace is treated as empty."""
        event = _make_event({"original_url": "   "})
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["error"], "URL is required")

    # ------------------------------------------------------------------
    # Validation — bad URL formats
    # ------------------------------------------------------------------

    def test_invalid_scheme_returns_400(self):
        """URLs without http/https scheme are rejected."""
        event = _make_event({"original_url": "ftp://example.com"})
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("http", body["error"])

    def test_no_scheme_returns_400(self):
        """Bare hostnames with no scheme are rejected."""
        event = _make_event({"original_url": "example.com/path"})
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 400)

    def test_no_domain_dot_returns_400(self):
        """URLs with netloc but no dot (e.g. 'https://localhost') are rejected."""
        event = _make_event({"original_url": "https://localhost"})
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("domain", body["error"])

    def test_plain_text_returns_400(self):
        """Arbitrary non-URL strings are rejected."""
        event = _make_event({"original_url": "not a url at all"})
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 400)

    # ------------------------------------------------------------------
    # Validation — malformed JSON body
    # ------------------------------------------------------------------

    def test_malformed_json_body_returns_400(self):
        """A body that is not valid JSON returns 400, not a 500 crash."""
        event = _make_event(raw_body="{this is not json}")
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["error"], "Invalid request body")

    def test_non_object_json_body_returns_400(self):
        """A JSON array body (not an object) is rejected with 400."""
        event = _make_event(raw_body='["https://example.com"]')
        result = self.handler(event, {})
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["error"], "Request body must be a JSON object")
    # ------------------------------------------------------------------
    # Collision retry logic
    # ------------------------------------------------------------------

    def test_collision_retry_succeeds_on_second_attempt(self):
        """
        If the first candidate short_id is already taken, the handler retries
        and succeeds with the second candidate.
        """
        import shorten as shorten_module
        import string

        # Pre-seed a known collision ID
        first_candidate = "AAAAAA"
        second_candidate = "BBBBBB"
        self.table.put_item(Item={
            "short_id": first_candidate,
            "original_url": "https://already-taken.com",
            "created_at": "2024-01-01T00:00:00+00:00",
            "clicks": 0,
            "expires_at": 9999999999,
        })

        # Make random.choices return the collision first, then a free ID
        call_count = {"n": 0}
        originals = [first_candidate, second_candidate]

        def fake_choices(population, k):
            idx = min(call_count["n"], len(originals) - 1)
            call_count["n"] += 1
            return list(originals[idx])

        with patch("random.choices", side_effect=fake_choices):
            event = _make_event({"original_url": "https://www.example.com"})
            result = self.handler(event, {})

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["short_id"], second_candidate)

    def test_all_retries_exhausted_returns_500(self):
        """
        If every generated candidate collides (all MAX_RETRIES attempts taken),
        the handler returns 500 rather than crashing.
        """
        # Pre-seed all three candidates the mock will return
        for collision_id in ["CCCCCC", "DDDDDD", "EEEEEE"]:
            self.table.put_item(Item={
                "short_id": collision_id,
                "original_url": "https://already-taken.com",
                "created_at": "2024-01-01T00:00:00+00:00",
                "clicks": 0,
                "expires_at": 9999999999,
            })

        candidates = ["CCCCCC", "DDDDDD", "EEEEEE"]
        call_count = {"n": 0}

        def fake_choices(population, k):
            result = list(candidates[call_count["n"] % len(candidates)])
            call_count["n"] += 1
            return result

        with patch("random.choices", side_effect=fake_choices):
            event = _make_event({"original_url": "https://www.example.com"})
            result = self.handler(event, {})

        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertIn("unique", body["error"])

    # ------------------------------------------------------------------
    # Response shape
    # ------------------------------------------------------------------

    def test_cors_header_present_on_success(self):
        """CORS header is present on 200 responses."""
        event = _make_event({"original_url": "https://www.example.com"})
        result = self.handler(event, {})
        self.assertEqual(result["headers"]["Access-Control-Allow-Origin"], "*")

    def test_cors_header_present_on_error(self):
        """CORS header is present on 400 error responses too."""
        event = _make_event({"original_url": ""})
        result = self.handler(event, {})
        self.assertEqual(result["headers"]["Access-Control-Allow-Origin"], "*")

    def test_ttl_expires_at_is_roughly_30_days_from_now(self):
        """expires_at stored in DynamoDB is approximately 30 days in the future."""
        from datetime import datetime, timezone, timedelta

        event = _make_event({"original_url": "https://www.example.com"})
        result = self.handler(event, {})
        body = json.loads(result["body"])
        short_id = body["short_id"]

        item = self.table.get_item(Key={"short_id": short_id}).get("Item")
        expires_at = int(item["expires_at"])

        now_ts = int(datetime.now(timezone.utc).timestamp())
        expected = now_ts + (30 * 24 * 3600)

        # Allow ±60 seconds tolerance for test execution time
        self.assertAlmostEqual(expires_at, expected, delta=60)


if __name__ == "__main__":
    unittest.main()
