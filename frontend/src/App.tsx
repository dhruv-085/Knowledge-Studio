import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowUp,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  FileText,
  FileUp,
  FolderOpen,
  LoaderCircle,
  Menu,
  MessageSquareText,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const SHORT_TECHNICAL_TERMS = new Set([
  "ai",
  "ml",
  "rag",
  "api",
  "sql",
  "pdf",
  "llm",
]);
type Conversation = {
  conversation_id: string;
  created_at?: string;
  first_message?: string | null;
};
type Message = {
  message_id: number;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  citations?: Citation[];
  retrieved_evidence?: Evidence[];
  refused?: boolean;
};
type Document = {
  document_id: string;
  filename: string;
  file_type: string;
  status: string;
  page_count: number | null;
};
type Citation = {
  document_id: string;
  document_name: string;
  source_path: string | null;
  page_number: number | null;
  section: string | null;
  passage_id: number;
};
type Evidence = Citation & { text: string; score: number; score_name: string };
type Turn = {
  message: Message;
  citations?: Citation[];
  evidence?: Evidence[];
  refused?: boolean;
};

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

function looksLikeAccidentalInput(text: string) {
  const words = text
    .split(/\s+/)
    .filter((word) => /[\p{L}\p{N}]/u.test(word))
    .map((word) => word.toLowerCase());
  return (
    !words.length ||
    text.length > 4000 ||
    words.every(
      (word) => word.length <= 2 && !SHORT_TECHNICAL_TERMS.has(word),
    ) ||
    (words.length > 1 && new Set(words).size === 1)
  );
}

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [messages, setMessages] = useState<Turn[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [openSources, setOpenSources] = useState<number | null>(null);
  const [connected, setConnected] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() =>
    window.matchMedia(
      "(max-width: 760px) and (hover: none) and (pointer: coarse)",
    ).matches,
  );
  const fileInput = useRef<HTMLInputElement>(null);
  const bottom = useRef<HTMLDivElement>(null);

  const refreshConversations = async () => {
    const items = await api<Conversation[]>("/conversations");
    setConversations(items);
    return items;
  };

  const openConversation = async (id: string) => {
    if (
      window.matchMedia(
        "(max-width: 760px) and (hover: none) and (pointer: coarse)",
      ).matches
    ) {
      setSidebarCollapsed(true);
    }
    setActive(id);
    setError("");
    setOpenSources(null);
    try {
      const [saved, docs] = await Promise.all([
        api<Message[]>(`/conversations/${id}/messages`),
        api<Document[]>(`/documents?conversation_id=${encodeURIComponent(id)}`),
      ]);
      setDocuments(docs);
      setMessages(
        saved.map((message) => ({
          message,
          citations:
            message.role === "assistant" ? message.citations : undefined,
          evidence:
            message.role === "assistant"
              ? message.retrieved_evidence
              : undefined,
          refused: message.role === "assistant" ? message.refused : undefined,
        })),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load this chat");
    }
  };

  const startNewChat = () => {
    if (
      window.matchMedia(
        "(max-width: 760px) and (hover: none) and (pointer: coarse)",
      ).matches
    ) {
      setSidebarCollapsed(true);
    }
    setError("");
    setActive(null);
    setMessages([]);
    setDocuments([]);
    setOpenSources(null);
  };

  const deleteConversation = async (id: string) => {
    try {
      await api<void>(`/conversations/${id}`, { method: "DELETE" });
      const remaining = conversations.filter(
        (item) => item.conversation_id !== id,
      );
      setConversations(remaining);
      if (active === id) {
        if (remaining.length)
          await openConversation(remaining[0].conversation_id);
        else startNewChat();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete this chat");
    }
  };

  useEffect(() => {
    refreshConversations()
      .then((items) => {
        setConnected(true);
        if (items.length) void openConversation(items[0].conversation_id);
      })
      .catch(() => {
        setConnected(false);
        setError(
          "Can’t reach the assistant API. Start the backend, then refresh this page.",
        );
      });
  }, []);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy, documents]);

  const uploadFiles = async (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    if (!files.length) return;
    setError("");
    setUploading(true);
    try {
      let conversationId = active;
      if (!conversationId) {
        const created = await api<{ conversation_id: string }>(
          "/conversations",
          { method: "POST" },
        );
        conversationId = created.conversation_id;
        setActive(conversationId);
        setMessages([]);
      }
      for (const file of files) {
        const form = new FormData();
        form.append("file", file);
        await api<Document>(
          `/documents?conversation_id=${encodeURIComponent(conversationId)}`,
          { method: "POST", body: form },
        );
      }
      const docs = await api<Document[]>(
        `/documents?conversation_id=${encodeURIComponent(conversationId)}`,
      );
      setDocuments(docs);
      await refreshConversations();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const sendQuestion = async (event: FormEvent) => {
    event.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    if (looksLikeAccidentalInput(text)) {
      setError(
        "That message looks incomplete. Please enter a question with a little more detail.",
      );
      return;
    }
    setQuestion("");
    setError("");
    setBusy(true);
    const temporaryId = Date.now();
    const now = new Date().toISOString();
    const draftId = active || `draft-${temporaryId}`;
    setMessages((previous) => [
      ...previous,
      {
        message: {
          message_id: temporaryId,
          conversation_id: draftId,
          role: "user",
          content: text,
          created_at: now,
        },
      },
    ]);
    let conversationId = active;
    try {
      if (!conversationId) {
        const created = await api<{ conversation_id: string }>(
          "/conversations",
          { method: "POST" },
        );
        conversationId = created.conversation_id;
        setActive(conversationId);
        setMessages((previous) =>
          previous.map((turn) =>
            turn.message.message_id === temporaryId
              ? {
                  ...turn,
                  message: {
                    ...turn.message,
                    conversation_id: conversationId!,
                  },
                }
              : turn,
          ),
        );
      }
      const result = await api<{
        conversation_id: string;
        answer: string;
        refused: boolean;
        citations: Citation[];
        retrieved_evidence: Evidence[];
      }>("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: text,
          conversation_id: conversationId,
        }),
      });
      setMessages((previous) => [
        ...previous,
        {
          message: {
            message_id: Date.now(),
            conversation_id: result.conversation_id,
            role: "assistant",
            content: result.answer,
            created_at: new Date().toISOString(),
          },
          citations: result.citations,
          evidence: result.retrieved_evidence,
          refused: result.refused,
        },
      ]);
      await refreshConversations();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not get an answer");
    } finally {
      setBusy(false);
    }
  };

  const activeConversation = conversations.find(
    (item) => item.conversation_id === active,
  );
  const shortDate = (value?: string) =>
    value
      ? new Intl.DateTimeFormat("en-IN", {
          month: "short",
          day: "numeric",
          timeZone: "Asia/Kolkata",
        }).format(new Date(value.endsWith("Z") ? value : `${value}Z`))
      : "New chat";
  const titleFor = (item: Conversation) =>
    item.first_message?.slice(0, 37) || "New conversation";
  const formatTime = (value: string) =>
    new Intl.DateTimeFormat("en-IN", {
      hour: "numeric",
      minute: "2-digit",
      timeZone: "Asia/Kolkata",
    }).format(new Date(value));

  return (
    <div className={`app-shell ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand">
            <div className="brand-mark">
              <BookOpen size={19} />
            </div>
            <div>
              <b>Leo</b>
              <span>KNOWLEDGE STUDIO</span>
            </div>
          </div>
          <div className="sidebar-controls">
            <button
              className="icon-button panel-toggle"
              title={
                sidebarCollapsed
                  ? "Expand workspace panel"
                  : "Minimize workspace panel"
              }
              aria-label={
                sidebarCollapsed
                  ? "Expand workspace panel"
                  : "Minimize workspace panel"
              }
              onClick={() => setSidebarCollapsed((value) => !value)}
            >
              {sidebarCollapsed ? (
                <PanelLeftOpen size={17} />
              ) : (
                <PanelLeftClose size={17} />
              )}
            </button>
          </div>
        </div>
        <button className="new-chat" onClick={startNewChat}>
          <Plus size={17} />
          <span>New chat</span>
        </button>
        <div className="side-label">YOUR WORKSPACE</div>
        <button className="nav-item active-nav">
          <MessageSquareText size={16} /> Conversations{" "}
          <span>{conversations.length}</span>
        </button>
        <div className="side-label recent-label">RECENT</div>
        <div className="conversation-list">
          {conversations.map((item) => (
            <div
              key={item.conversation_id}
              className={`conversation-row ${active === item.conversation_id ? "selected" : ""}`}
            >
              <button
                className="conversation-item"
                onClick={() => void openConversation(item.conversation_id)}
              >
                <MessageSquareText size={15} />
                <span>{titleFor(item)}</span>
                <small>{shortDate(item.created_at)}</small>
              </button>
              <button
                className="delete-chat"
                title="Delete chat"
                aria-label={`Delete ${titleFor(item)}`}
                onClick={() => void deleteConversation(item.conversation_id)}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
        <div className="sidebar-bottom">
          <div className="api-status">
            <span className={connected ? "status-dot" : "status-dot offline"} />
            <span>{connected ? "Assistant ready" : "API unavailable"}</span>
            <Activity size={14} />
          </div>
          <div className="profile">
            <div className="avatar">K</div>
            <div>
              <b>Knowledge workspace</b>
              <span>Local and private</span>
            </div>
          </div>
        </div>
      </aside>
      {!sidebarCollapsed && (
        <button
          className="sidebar-backdrop"
          aria-label="Close workspace menu"
          onClick={() => setSidebarCollapsed(true)}
        />
      )}

      <main className="main-panel">
        <header className="topbar">
          <button
            className="icon-button mobile-menu-toggle"
            title="Open workspace menu"
            aria-label="Open workspace menu"
            onClick={() => setSidebarCollapsed(false)}
          >
            <Menu size={18} />
          </button>
          <div className="breadcrumb">
            <span>Workspace</span>
            <ChevronRight size={14} />
            <b>
              {activeConversation
                ? titleFor(activeConversation)
                : "New conversation"}
            </b>
          </div>
          <div className="top-actions">
            <span className="model-pill">
              <span className="model-dot" /> Grounded answers
            </span>
          </div>
        </header>

        <section className="conversation-area">
          <div className="chat-column">
            {messages.length === 0 && documents.length === 0 ? (
              <div className="welcome">
                <div className="welcome-orb">
                  <Sparkles size={21} />
                </div>
                <div className="eyebrow">
                  YOUR TECHNICAL KNOWLEDGE, CONNECTED
                </div>
                <h1>
                  Good questions start
                  <br />
                  with <em>good context.</em>
                </h1>
                <p>
                  Bring your docs into the conversation. Ask naturally.
                  <br />
                  Every answer is grounded in your sources.
                </p>
                <div className="welcome-actions">
                  <button onClick={() => fileInput.current?.click()}>
                    <FileUp size={16} /> Add documents
                  </button>
                  <span>PDF · TXT · Markdown</span>
                </div>
              </div>
            ) : (
              <div className="message-feed">
                {documents.length > 0 && (
                  <div className="attached-docs">
                    <div className="attached-title">
                      <FolderOpen size={15} />
                      <span>IN THIS CHAT</span>
                      <i>
                        {documents.length}{" "}
                        {documents.length === 1 ? "source" : "sources"}
                      </i>
                    </div>
                    <div className="document-chips">
                      {documents.map((doc) => (
                        <div className="document-chip" key={doc.document_id}>
                          <div className="file-icon">
                            <FileText size={15} />
                          </div>
                          <div className="file-meta">
                            <b>{doc.filename}</b>
                            <span>
                              {doc.file_type.toUpperCase()}
                              {doc.page_count
                                ? ` · ${doc.page_count} pages`
                                : ""}
                            </span>
                          </div>
                          <Check size={14} className="file-check" />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {messages.map((turn, index) => (
                  <div
                    className={`turn ${turn.message.role}`}
                    key={turn.message.message_id}
                  >
                    {turn.message.role === "assistant" && (
                      <div className="assistant-icon">
                        <Sparkles size={15} />
                      </div>
                    )}
                    <div className="turn-body">
                      <div className="turn-label">
                        {turn.message.role === "user" ? "YOU" : "LEO"}{" "}
                        <span>{formatTime(turn.message.created_at)}</span>
                      </div>
                      <div
                        className={`message-bubble ${turn.message.role} ${turn.refused ? "refused" : ""}`}
                      >
                        {turn.message.content}
                      </div>
                      {turn.message.role === "assistant" &&
                      (turn.citations?.length || turn.evidence?.length) ? (
                        <div className="source-block">
                          <button
                            className="source-toggle"
                            onClick={() =>
                              setOpenSources(
                                openSources === index ? null : index,
                              )
                            }
                          >
                            <BookOpen size={14} />
                            {turn.citations?.length ||
                              turn.evidence?.length}{" "}
                            sources used
                            {openSources === index ? (
                              <ChevronDown size={14} />
                            ) : (
                              <ChevronRight size={14} />
                            )}
                          </button>
                          {openSources === index && (
                            <div className="source-list">
                              {(turn.citations || []).map((citation) => {
                                const evidence = turn.evidence?.find(
                                  (item) =>
                                    item.passage_id === citation.passage_id,
                                );
                                return (
                                  <article
                                    className="source-card"
                                    key={`${citation.document_id}-${citation.passage_id}`}
                                  >
                                    <div className="source-card-head">
                                      <span>
                                        <FileText size={13} />
                                        {citation.document_name}
                                        {citation.page_number
                                          ? ` · p. ${citation.page_number}`
                                          : ""}
                                      </span>
                                      <small>
                                        PASSAGE {citation.passage_id}
                                      </small>
                                    </div>
                                    {evidence && <p>“{evidence.text}”</p>}
                                  </article>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      ) : null}
                    </div>
                    {turn.message.role === "user" && (
                      <div className="user-avatar">K</div>
                    )}
                  </div>
                ))}
                {uploading && (
                  <div className="activity-line">
                    <LoaderCircle size={15} className="spin" /> Adding sources
                    to this chat…
                  </div>
                )}
                {busy && (
                  <div className="turn assistant">
                    <div className="assistant-icon">
                      <Sparkles size={15} />
                    </div>
                    <div className="turn-body">
                      <div className="turn-label">
                        LEO <span>THINKING</span>
                      </div>
                      <div className="message-bubble pending">
                        <i />
                        <i />
                        <i />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={bottom} />
              </div>
            )}

            {error && (
              <div className="error-banner">
                <span>{error}</span>
                <button onClick={() => setError("")} aria-label="Dismiss">
                  <X size={15} />
                </button>
              </div>
            )}
            <div className="composer-wrap">
              <form className="composer" onSubmit={sendQuestion}>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void sendQuestion(e as unknown as FormEvent);
                    }
                  }}
                  placeholder={
                    documents.length
                      ? "Ask anything about your sources…"
                      : "Add a document to this chat to get started…"
                  }
                  rows={2}
                />
                <div className="composer-tools">
                  <div className="composer-hint">
                    <button
                      type="button"
                      className="attach-button"
                      onClick={() => fileInput.current?.click()}
                      disabled={uploading}
                    >
                      <Plus size={16} />
                      <span>Add sources</span>
                    </button>
                    <span className="hint-divider" />{" "}
                    <span>Answers grounded in this chat’s sources</span>
                  </div>
                  <button
                    className="send-button"
                    type="submit"
                    disabled={!question.trim() || busy || !documents.length}
                    title="Send message"
                  >
                    {busy ? (
                      <LoaderCircle size={17} className="spin" />
                    ) : (
                      <ArrowUp size={18} />
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </section>
        <input
          ref={fileInput}
          type="file"
          accept=".pdf,.txt,.md,.markdown"
          multiple
          hidden
          onChange={uploadFiles}
        />
      </main>
    </div>
  );
}

export default App;
