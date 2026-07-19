"""Genie seam — autonomous, multi-step data tasks (NL -> governed SQL).

Optional to the core Referral Copilot flow, but part of the required stack.
Useful for planner-style questions ("how many documented ICUs within 50km of
Patna?") and for regional coverage aggregates. Returns None when unavailable
or on any failure, so a broken/unauthorized Genie call degrades to "not
answered" rather than breaking the live demo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .config import BackendConfig


class GenieConversationClient(Protocol):
    """The slice of databricks.sdk.WorkspaceClient.genie this module calls.

    Kept as a narrow protocol (rather than importing the SDK type) so tests can
    inject a fake without the real package installed.
    """

    def start_conversation_and_wait(self, space_id: str, content: str) -> Any: ...

    def create_message_and_wait(self, space_id: str, conversation_id: str, content: str) -> Any: ...

    def get_message_attachment_query_result(
        self, space_id: str, conversation_id: str, message_id: str, attachment_id: str
    ) -> Any: ...


@dataclass(frozen=True)
class GenieAnswer:
    """Display-shaped result: the generated SQL is part of the evidence trail."""

    answer: str | None
    sql: str | None
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    conversation_id: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "sql": self.sql,
            "columns": list(self.columns),
            "rows": [dict(row) for row in self.rows],
            "conversation_id": self.conversation_id,
        }


class GenieClient:
    def __init__(
        self,
        config: BackendConfig,
        *,
        client_factory: "Any | None" = None,
    ) -> None:
        self._config = config
        # Lazily built so importing this module never requires the SDK to be
        # installed/authenticated; `client_factory` lets tests inject a fake.
        self._client_factory = client_factory
        self._client: GenieConversationClient | None = None

    def available(self) -> bool:
        return self._config.has_genie

    def _genie(self) -> GenieConversationClient | None:
        if self._client is not None:
            return self._client
        try:
            if self._client_factory is not None:
                workspace = self._client_factory()
            else:
                from databricks.sdk import WorkspaceClient  # local import: optional dep

                # Databricks Apps inject the app's service-principal auth via
                # env/config automatically; no token is read here.
                workspace = WorkspaceClient()
            self._client = workspace.genie
        except Exception:
            self._client = None
        return self._client

    def ask(self, question: str, *, conversation_id: str | None = None) -> dict[str, Any] | None:
        """Answer a natural-language data question, or None if unavailable.

        Starts (or continues) a Genie conversation against the facility tables'
        space, waits for Genie to generate + run SQL, and returns
        {"answer", "sql", "columns", "rows", "conversation_id"} so the UI can
        show the generated SQL as part of the evidence trail. `conversation_id`
        lets a caller continue a multi-turn planner conversation instead of
        starting a new one each time.
        """
        question = (question or "").strip()
        if not self.available() or not question:
            return None

        genie = self._genie()
        if genie is None:
            return None

        space_id = self._config.genie_space_id
        try:
            if conversation_id:
                message = genie.create_message_and_wait(
                    space_id=space_id, conversation_id=conversation_id, content=question
                )
            else:
                message = genie.start_conversation_and_wait(space_id=space_id, content=question)
        except Exception:
            return None

        answer = self._to_answer(genie, space_id, message)
        return answer.as_dict() if answer is not None else None

    def _to_answer(self, genie: GenieConversationClient, space_id: str, message: Any) -> GenieAnswer | None:
        msg_conversation_id = getattr(message, "conversation_id", None)
        msg_id = getattr(message, "id", None) or getattr(message, "message_id", None)
        answer_text: str | None = None
        sql: str | None = None
        columns: tuple[str, ...] = ()
        rows: tuple[dict[str, Any], ...] = ()

        for attachment in getattr(message, "attachments", None) or []:
            text = getattr(attachment, "text", None)
            content = getattr(text, "content", None) if text is not None else None
            if content:
                answer_text = content

            query = getattr(attachment, "query", None)
            query_sql = getattr(query, "query", None) if query is not None else None
            if not query_sql:
                continue
            sql = query_sql

            attachment_id = getattr(attachment, "attachment_id", None)
            if not (msg_conversation_id and msg_id and attachment_id):
                continue
            try:
                result = genie.get_message_attachment_query_result(
                    space_id=space_id,
                    conversation_id=msg_conversation_id,
                    message_id=msg_id,
                    attachment_id=attachment_id,
                )
            except Exception:
                continue
            columns, rows = _rows_from_statement_response(getattr(result, "statement_response", None))

        if answer_text is None and sql is None:
            return None

        return GenieAnswer(
            answer=answer_text,
            sql=sql,
            columns=columns,
            rows=rows,
            conversation_id=msg_conversation_id,
        )


def _rows_from_statement_response(statement_response: Any) -> tuple[tuple[str, ...], tuple[dict[str, Any], ...]]:
    """Flatten a Databricks SQL statement response into column names + row dicts."""
    if statement_response is None:
        return (), ()

    manifest = getattr(statement_response, "manifest", None)
    schema = getattr(manifest, "schema", None) if manifest is not None else None
    raw_columns = getattr(schema, "columns", None) if schema is not None else None
    columns = tuple(getattr(c, "name", "") for c in raw_columns) if raw_columns else ()
    if not columns:
        return (), ()

    result = getattr(statement_response, "result", None)
    data_array = getattr(result, "data_array", None) if result is not None else None
    rows = tuple(dict(zip(columns, row)) for row in data_array) if data_array else ()
    return columns, rows
