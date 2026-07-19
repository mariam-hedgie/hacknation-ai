"""Contract tests for the Genie seam (NL question -> generated SQL -> rows)."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_ROOT))

from src.backend.config import BackendConfig  # noqa: E402
from src.backend.genie import GenieClient  # noqa: E402


def _config(genie_space_id: str = "space-1") -> BackendConfig:
    return BackendConfig.from_env({"AVEN_GENIE_SPACE_ID": genie_space_id})


def _attachment(*, text: str | None = None, sql: str | None = None, attachment_id: str = "att-1") -> object:
    return types.SimpleNamespace(
        attachment_id=attachment_id,
        text=types.SimpleNamespace(content=text) if text is not None else None,
        query=types.SimpleNamespace(query=sql) if sql is not None else None,
    )


def _message(*, conversation_id: str = "conv-1", message_id: str = "msg-1", attachments: list[object]) -> object:
    return types.SimpleNamespace(conversation_id=conversation_id, id=message_id, attachments=attachments)


def _statement_response(columns: list[str], data_array: list[list[object]]) -> object:
    schema = types.SimpleNamespace(columns=[types.SimpleNamespace(name=c) for c in columns])
    manifest = types.SimpleNamespace(schema=schema)
    result = types.SimpleNamespace(data_array=data_array)
    return types.SimpleNamespace(manifest=manifest, result=result)


class FakeGenie:
    """Stands in for WorkspaceClient().genie in tests."""

    def __init__(self, message: object, statement_response: object | None = None, *, raise_on_start: bool = False) -> None:
        self.message = message
        self.statement_response = statement_response
        self.raise_on_start = raise_on_start
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def start_conversation_and_wait(self, space_id: str, content: str) -> object:
        self.calls.append(("start_conversation_and_wait", (space_id, content)))
        if self.raise_on_start:
            raise ConnectionError("genie unavailable")
        return self.message

    def create_message_and_wait(self, space_id: str, conversation_id: str, content: str) -> object:
        self.calls.append(("create_message_and_wait", (space_id, conversation_id, content)))
        return self.message

    def get_message_attachment_query_result(
        self, space_id: str, conversation_id: str, message_id: str, attachment_id: str
    ) -> object:
        self.calls.append(
            ("get_message_attachment_query_result", (space_id, conversation_id, message_id, attachment_id))
        )
        if self.statement_response is None:
            raise ValueError("no result")
        return types.SimpleNamespace(statement_response=self.statement_response)


class GenieAvailabilityTests(unittest.TestCase):
    def test_unavailable_without_a_configured_space(self) -> None:
        client = GenieClient(_config(genie_space_id=""))

        self.assertFalse(client.available())
        self.assertIsNone(client.ask("How many facilities document dialysis?"))

    def test_blank_question_is_never_sent(self) -> None:
        fake = FakeGenie(_message(attachments=[]))
        client = GenieClient(_config(), client_factory=lambda: types.SimpleNamespace(genie=fake))

        self.assertIsNone(client.ask("   "))
        self.assertEqual(fake.calls, [])


class GenieAskTests(unittest.TestCase):
    def test_returns_answer_sql_and_rows_from_a_new_conversation(self) -> None:
        statement_response = _statement_response(
            ["facility_id", "documented_count"], [["patna-01", 3], ["patna-02", 1]]
        )
        message = _message(
            attachments=[
                _attachment(text="2 facilities document dialysis near Patna."),
                _attachment(sql="SELECT facility_id, documented_count FROM facility_trust_assessment ..."),
            ]
        )
        fake = FakeGenie(message, statement_response)
        client = GenieClient(_config(), client_factory=lambda: types.SimpleNamespace(genie=fake))

        result = client.ask("How many facilities document dialysis near Patna?")

        self.assertEqual(result["answer"], "2 facilities document dialysis near Patna.")
        self.assertIn("facility_trust_assessment", result["sql"])
        self.assertEqual(result["columns"], ["facility_id", "documented_count"])
        self.assertEqual(
            result["rows"],
            [
                {"facility_id": "patna-01", "documented_count": 3},
                {"facility_id": "patna-02", "documented_count": 1},
            ],
        )
        self.assertEqual(result["conversation_id"], "conv-1")
        self.assertEqual(fake.calls[0][0], "start_conversation_and_wait")

    def test_continues_an_existing_conversation_when_a_conversation_id_is_given(self) -> None:
        fake = FakeGenie(_message(attachments=[_attachment(text="Yes, three within 50km.")]))
        client = GenieClient(_config(), client_factory=lambda: types.SimpleNamespace(genie=fake))

        client.ask("And within 50km?", conversation_id="conv-1")

        self.assertEqual(fake.calls[0], ("create_message_and_wait", ("space-1", "conv-1", "And within 50km?")))

    def test_start_failure_returns_none_instead_of_raising(self) -> None:
        fake = FakeGenie(_message(attachments=[]), raise_on_start=True)
        client = GenieClient(_config(), client_factory=lambda: types.SimpleNamespace(genie=fake))

        self.assertIsNone(client.ask("How many facilities document dialysis?"))

    def test_query_result_failure_still_returns_the_answer_text(self) -> None:
        message = _message(
            attachments=[
                _attachment(text="Here is what I found."),
                _attachment(sql="SELECT 1"),
            ]
        )
        fake = FakeGenie(message, statement_response=None)
        client = GenieClient(_config(), client_factory=lambda: types.SimpleNamespace(genie=fake))

        result = client.ask("Any dialysis units?")

        self.assertEqual(result["answer"], "Here is what I found.")
        self.assertEqual(result["sql"], "SELECT 1")
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["columns"], [])

    def test_no_usable_attachment_returns_none(self) -> None:
        fake = FakeGenie(_message(attachments=[_attachment()]))
        client = GenieClient(_config(), client_factory=lambda: types.SimpleNamespace(genie=fake))

        self.assertIsNone(client.ask("Anything?"))

    def test_client_factory_failure_is_treated_as_unavailable(self) -> None:
        def _boom() -> object:
            raise RuntimeError("no workspace auth")

        client = GenieClient(_config(), client_factory=_boom)

        self.assertIsNone(client.ask("How many facilities document dialysis?"))


if __name__ == "__main__":
    unittest.main()
