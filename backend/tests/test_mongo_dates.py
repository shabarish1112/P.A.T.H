from datetime import UTC, datetime, timedelta
from unittest import TestCase
from unittest.mock import patch

from bson import BSON
from pymongo import MongoClient

from app.core.config import Settings
from app.db.mongo import get_client, reset_db_for_tests


class MongoDateTests(TestCase):
    def tearDown(self) -> None:
        reset_db_for_tests()

    def test_stored_token_expiry_can_be_compared_with_utc_now(self) -> None:
        settings = Settings(
            mongo_uri='mongodb://user:pass@localhost:27017/path',
            jwt_secret='test-signing-key-with-at-least-32-characters',
        )
        with patch(
            'app.db.mongo.MongoClient',
            side_effect=lambda *args, **kwargs: MongoClient(
                *args,
                **kwargs,
                connect=False,
            ),
        ):
            client = get_client(settings)
        expires_at = datetime.now(UTC) + timedelta(days=1)
        stored = BSON.encode({'expires_at': expires_at}).decode(codec_options=client.codec_options)
        self.assertIsNotNone(stored['expires_at'].tzinfo)
        self.assertGreater(stored['expires_at'], datetime.now(UTC))
