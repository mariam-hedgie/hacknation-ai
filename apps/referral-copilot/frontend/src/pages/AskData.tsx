import { useEffect, useState } from "react";
import { api, type AskResult } from "../api";

interface Turn {
  question: string;
  result: NonNullable<AskResult["result"]>;
}

export function AskData() {
  const [genieAvailable, setGenieAvailable] = useState(false);
  const [localAskAvailable, setLocalAskAvailable] = useState(false);
  const [statusLoaded, setStatusLoaded] = useState(false);
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [history, setHistory] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(false);
  const [notAnswered, setNotAnswered] = useState(false);

  const askAvailable = genieAvailable || localAskAvailable;

  useEffect(() => {
    api
      .serviceStatus()
      .then((s) => {
        setGenieAvailable(Boolean(s.tools.genie));
        setLocalAskAvailable(Boolean(s.tools.local_ask));
      })
      .catch(() => {
        setGenieAvailable(false);
        setLocalAskAvailable(false);
      })
      .finally(() => setStatusLoaded(true));
  }, []);

  const ask = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setNotAnswered(false);
    try {
      const response = await api.ask(question, conversationId);
      if (!response.answered || !response.result) {
        setNotAnswered(true);
        return;
      }
      setConversationId(response.result.conversation_id ?? null);
      setHistory((prev) => [{ question, result: response.result! }, ...prev]);
      setQuestion("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page flow-page">
      <div className="section-title" style={{ marginBottom: "0.6rem" }}>
        Planner data questions
      </div>
      <h2>Ask Aven about the data</h2>
      <p className="hint" style={{ maxWidth: "70ch" }}>
        Aven turns this into governed SQL over the facility tables via Databricks Genie and shows the query it ran —
        this is aggregate/coverage data, not a personal care plan.
      </p>

      {statusLoaded && !genieAvailable && localAskAvailable && (
        <div className="datasource-note">
          Genie is not connected in this environment, so questions are answered against a local snapshot instead
          (data/facilities_searchable.json) — real facility data, not a live Databricks connection.
        </div>
      )}
      {statusLoaded && !askAvailable && (
        <div className="datasource-note">
          Neither Genie nor the local fallback is configured (need AVEN_GENIE_SPACE_ID + a SQL warehouse, or
          OPENAI_API_KEY + a local data snapshot), so this page can't answer yet.
        </div>
      )}

      <div className="form-card" style={{ marginTop: "1rem" }}>
        <div className="field">
          <label>Your question</label>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How many facilities near Patna document dialysis?"
            onKeyDown={(e) => e.key === "Enter" && ask()}
          />
        </div>
        <button className="btn btn-primary" onClick={ask} disabled={!askAvailable || loading}>
          {loading && <span className="spinner" />} Ask
        </button>
      </div>

      {notAnswered && (
        <div className="alert alert-warning">
          Aven could not answer that — try rephrasing, or asking about a specific capability/procedure.
        </div>
      )}

      {history.map((turn, i) => (
        <div className="ask-turn" key={i}>
          <p className="fact">
            <strong>You asked:</strong> {turn.question}
          </p>
          {turn.result.answer && <p>{turn.result.answer}</p>}
          {turn.result.sql && (
            <details className="disclosure">
              <summary>Generated SQL (the evidence for this answer)</summary>
              <pre className="sql-block">{turn.result.sql}</pre>
            </details>
          )}
          {turn.result.rows && turn.result.rows.length > 0 && (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    {Object.keys(turn.result.rows[0]).map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {turn.result.rows.map((row, r) => (
                    <tr key={r}>
                      {Object.keys(turn.result.rows![0]).map((col) => (
                        <td key={col}>{String(row[col])}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}

      {history.length > 0 && (
        <button
          className="btn"
          onClick={() => {
            setConversationId(null);
            setHistory([]);
          }}
        >
          Clear conversation
        </button>
      )}
    </div>
  );
}
