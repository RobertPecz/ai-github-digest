import base64
from email import policy
from email.parser import BytesParser
import unittest
from unittest.mock import Mock, patch

from ai_digest.gmail import send_gmail
from ai_digest.settings import GmailSettings


class TestGmail(unittest.TestCase):
    def setUp(self):
        self.config = GmailSettings("id", "secret", "refresh", "from@example.com", "to@example.com")
        self.token = Mock(ok=True)
        self.token.json.return_value = {"access_token": "access"}

    def test_send_confirms_message_id_and_preserves_mime_content(self):
        with patch("ai_digest.gmail.requests.post", return_value=self.token) as refresh, \
             patch("ai_digest.gmail.request_json", return_value={"id": "msg-1"}) as send:
            result = send_gmail("Tárgy", "Árvíztűrő", "<b>HTML</b>", self.config)
        self.assertEqual(result, "msg-1")
        self.assertEqual(refresh.call_args.kwargs["data"]["grant_type"], "refresh_token")
        self.assertEqual(send.call_args.kwargs["headers"]["Authorization"], "Bearer access")
        message = BytesParser(policy=policy.default).parsebytes(
            base64.urlsafe_b64decode(send.call_args.kwargs["data"]["raw"])
        )
        self.assertEqual(message["Subject"], "Tárgy")
        self.assertEqual(message["To"], "to@example.com")
        self.assertEqual(message.get_body(preferencelist=("plain",)).get_content().strip(), "Árvíztűrő")
        self.assertEqual(message.get_body(preferencelist=("html",)).get_content().strip(), "<b>HTML</b>")

    def test_missing_configuration_fails_before_network_access(self):
        with patch("ai_digest.gmail.requests.post") as post:
            with self.assertRaisesRegex(RuntimeError, "Missing Gmail environment variable"):
                send_gmail("Subject", "Plain", "HTML", GmailSettings())
            post.assert_not_called()

    def test_unconfirmed_send_is_error(self):
        with patch("ai_digest.gmail.requests.post", return_value=self.token), \
             patch("ai_digest.gmail.request_json", return_value={}):
            with self.assertRaisesRegex(RuntimeError, "unconfirmed"):
                send_gmail("Subject", "Plain", "HTML", self.config)

    def test_oauth_errors_prevent_delivery(self):
        for response in (Mock(ok=False, status_code=400), Mock(ok=True, json=lambda: {})):
            with self.subTest(response=response), \
                 patch("ai_digest.gmail.requests.post", return_value=response), \
                 patch("ai_digest.gmail.request_json") as send:
                with self.assertRaises(RuntimeError):
                    send_gmail("Subject", "Plain", "HTML", self.config)
                send.assert_not_called()
