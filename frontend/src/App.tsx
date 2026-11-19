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
import {
  clearConversations,
  getAllConversations,
  getConversation,
  importConversations,
  removeConversation,
  saveConversation,
  type LocalRecord,
} from "./localStore";

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
  documents: Document[];
  turns: Turn[];
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
  text: string;
  page_texts: { page_number: number; text: string }[];
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
    let message = `Request failed (${response.status})`;
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body.detail) && body.detail.length > 0) {
      message = body.detail.map((err: { msg?: string }) => err.msg || JSON.stringify(err)).join(", ");
    }
    throw new Error(message);
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
  const importInput = useRef<HTMLInputElement>(null);
  const bottom = useRef<HTMLDivElement>(null);

  const recordFor = (id: string, docs = documents, turns = messages): LocalRecord => ({
    conversation_id: id,
    created_at: conversations.find((item) => item.conversation_id === id)?.created_at || new Date().toISOString(),
    first_message: turns.find((turn) => turn.message.role === "user")?.message.content || null,
    documents: docs,
    messages: turns,
  });

  const refreshConversations = async () => {
    const records = await getAllConversations();
    const items: Conversation[] = records.sort((a, b) => b.created_at.localeCompare(a.created_at)).map((record) => ({
      conversation_id: record.conversation_id,
      created_at: record.created_at,
      first_message: record.first_message,
      documents: record.documents as Document[],
      turns: record.messages as Turn[],
    }));
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
      const record = await getConversation(id);
      if (!record) throw new Error("This conversation is no longer in this browser");
      setDocuments(record.documents as Document[]);
      setMessages(record.messages as Turn[]);
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
    setQuestion("");
    setOpenSources(null);
  };

  const deleteConversation = async (id: string) => {
    try {
      await removeConversation(id);
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
    void refreshConversations()
      .then((items) => {
        if (items.length) void openConversation(items[0].conversation_id);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Could not read this browser's saved chats"));
    void api<{ status: string }>("/health")
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
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
    let conversationId = active;
    let createdNewConversation = false;
    let currentDocs = documents;
    try {
      if (!conversationId) {
        conversationId = crypto.randomUUID();
        createdNewConversation = true;
        setActive(conversationId);
        setMessages([]);
        await saveConversation(recordFor(conversationId, [], []));
      }
      if (currentDocs.length + files.length > 10) {
        throw new Error("A conversation can contain up to 10 documents.");
      }
      const oversizedFile = files.find((file) => file.size > 20 * 1024 * 1024);
      if (oversizedFile) {
        throw new Error(`${oversizedFile.name} is larger than the 20 MiB upload limit.`);
      }
      for (const file of files) {
        if (currentDocs.length >= 10) {
          throw new Error("A conversation can contain up to 10 documents.");
        }
        const form = new FormData();
        form.append("file", file);
        const document = await api<Document>(
          "/documents",
          { method: "POST", body: form },
        );
        const next = [...currentDocs, document];
        if (next.reduce((sum, item) => sum + item.text.length, 0) > 800_000) {
          throw new Error("Combined extracted text for this conversation cannot exceed 800,000 characters.");
        }
        currentDocs = next;
        setDocuments(next);
        await saveConversation(recordFor(conversationId, next, messages));
      }
      await refreshConversations();
    } catch (e) {
      if (createdNewConversation && conversationId && !currentDocs.length) {
        await removeConversation(conversationId);
        setActive(null);
      } else {
        await refreshConversations().catch(() => undefined);
      }
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const sendQuestion = async (event: FormEvent) => {
    event.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    if (!documents.length) {
      setError("Please add at least one document before asking a question.");
      return;
    }
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
    const userTurn: Turn = {
      message: {
        message_id: temporaryId,
        conversation_id: draftId,
        role: "user",
        content: text,
        created_at: now,
      },
    };
    const historyBeforeQuestion = messages;
    setMessages((previous) => [
      ...previous,
      userTurn,
    ]);
    let conversationId = active;
    try {
      if (!conversationId) {
        conversationId = crypto.randomUUID();
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
      const nextUserTurn = { ...userTurn, message: { ...userTurn.message, conversation_id: conversationId } };
      const before = [...historyBeforeQuestion];
      const withUser = [...before, nextUserTurn];
      await saveConversation(recordFor(conversationId, documents, withUser));
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
          documents: documents.map((document) => ({
            document_id: document.document_id,
            document_name: document.filename,
            text: document.text,
            page_texts: document.page_texts,
          })),
          history: before.slice(-12).map((turn) => ({
            role: turn.message.role,
            content: turn.message.content,
          })),
        }),
        signal: AbortSignal.timeout(180_000),
      });
      const assistantTurn: Turn = {
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
      };
      const finalTurns = [...withUser, assistantTurn];
      setMessages(finalTurns);
      await saveConversation(recordFor(conversationId, documents, finalTurns));
      await refreshConversations();
    } catch (e) {
      const restoredTurns = messages.filter((turn) => turn.message.message_id !== temporaryId);
      setMessages(restoredTurns);
      if (conversationId) {
        void saveConversation(recordFor(conversationId, documents, restoredTurns));
      }
      setQuestion(text);
      setError(e instanceof Error ? e.message : "Could not get an answer");
    } finally {
      setBusy(false);
    }
  };

  const importData = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    try {
      const text = await file.text();
      const data = JSON.parse(text) as unknown;

      const rawRecords =
        Array.isArray(data)
          ? data
          : data && typeof data === "object" && "conversations" in data && Array.isArray((data as { conversations: unknown }).conversations)
            ? (data as { conversations: unknown[] }).conversations
            : null;

      if (!rawRecords || !rawRecords.length) {
        throw new Error("Invalid backup file: expected a JSON file with saved conversations.");
      }

      const validRecords: LocalRecord[] = rawRecords.filter(
        (r): r is LocalRecord =>
          Boolean(
            r &&
              typeof r === "object" &&
              "conversation_id" in r &&
              typeof (r as { conversation_id: unknown }).conversation_id === "string" &&
              "messages" in r &&
              Array.isArray((r as { messages: unknown }).messages),
          ),
      );

      if (!validRecords.length) {
        throw new Error("No valid conversation records found in this backup file.");
      }

      await importConversations(validRecords);
      const updated = await refreshConversations();
      if (updated.length) {
        await openConversation(validRecords[0].conversation_id);
      }
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not import backup data");
    }
  };

  const exportData = async () => {
    const records = await getAllConversations();
    const file = new Blob([JSON.stringify({ exported_at: new Date().toISOString(), conversations: records }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(file);
    const link = document.createElement("a");
    link.href = url;
    link.download = "leo-browser-data.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  const clearAllData = async () => {
    if (!window.confirm("Delete every saved conversation and uploaded document from this browser? This cannot be undone.")) return;
    await clearConversations();
    setConversations([]);
    startNewChat();
    setError("");
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
        <button className="new-chat" onClick={startNewChat} disabled={busy || uploading}>
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
                disabled={busy || uploading}
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
                disabled={busy || uploading}
                onClick={() => void deleteConversation(item.conversation_id)}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
        <div className="local-data-controls">
          <input
            type="file"
            ref={importInput}
            accept="application/json,.json"
            style={{ display: "none" }}
            onChange={(e) => void importData(e)}
          />
          <button onClick={() => importInput.current?.click()} disabled={busy || uploading}>
            Import browser data
          </button>
          <button onClick={() => void exportData()} disabled={!conversations.length}>Export browser data</button>
          <button onClick={() => void clearAllData()} disabled={!conversations.length}>Clear all browser data</button>
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
              <span>Saved in this browser</span>
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
            <div className="privacy-notice" role="note">
              <b>Your data stays in this browser.</b> Documents and chats are saved in this browser profile and can be lost if its data is cleared. When you ask a question, selected document text and recent turns are sent to the assistant service; relevant evidence is sent to Gemini when configured. Don’t upload information you are not allowed to share.
            </div>
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
                  <button onClick={() => fileInput.current?.click()} disabled={busy || uploading}>
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
                  disabled={busy || uploading}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      if (!documents.length) {
                        setError("Please add at least one document before asking a question.");
                        return;
                      }
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
                      disabled={busy || uploading}
                    >
                      <Plus size={16} />
                      <span>Add sources</span>
                    </button>
                    <span className="hint-divider" />{" "}
                    <span>Answers grounded in this chat’s sources · first reply may take a moment</span>
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
          disabled={busy || uploading}
          onChange={uploadFiles}
        />
      </main>
    </div>
  );
}

export default App;
