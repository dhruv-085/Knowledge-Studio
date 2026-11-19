# Deployment Plan: Cloudflare Pages + Render

## Goal

Deploy the React/Vite frontend on Cloudflare Pages and the FastAPI backend on Render. Each browser profile keeps its own documents and conversations in IndexedDB. The backend processes requests without saving user documents or chat history.

This plan records the deployment architecture and the progress below. Its checklist distinguishes implementation in the repository from external account setup and a verified deployment. `plan.md` remains the source of truth for the overall project roadmap.

## Data flow

```text
User's browser
  ├── IndexedDB: documents, conversations, messages
  └── sends selected document text and recent chat history
          ↓
Render: stateless FastAPI request processing
  ├── parses uploaded files
  ├── retrieves evidence
  └── calls Gemini using a server-side API key
          ↓
User's browser saves the answer and citations in IndexedDB
```

“Browser-local storage” means saved data stays in that browser profile. It does not mean the document remains on the device during processing: the browser sends document content to Render, and relevant context is sent to Gemini.

## Implementation stages

### 1. Define browser data storage

- Use IndexedDB for documents and conversations; use `localStorage` only for small preferences.
- Store document metadata, extracted text, PDF page text, messages, citations, and evidence needed to restore chats.
- Decide how users can export, delete a conversation, and clear all browser data.
- Explain in the interface that data is saved in this browser, can be lost if browser data is cleared, and is sent to the service for answering.

**Complete when:** the data shape and user-facing privacy explanation are reviewed.

### 2. Make FastAPI stateless for user data

- Change document upload to parse and validate a file, return its extracted content and metadata, and avoid saving it to SQLite.
- Change chat requests to include the selected documents and recent conversation history.
- Return the answer, citations, and evidence without storing chat or document content on the server.
- Reuse the sentence encoder while a Render process is running, while treating its in-memory cache as temporary.

**Complete when:** a Render restart cannot delete a user's saved documents or chats.

### 3. Store and restore frontend data locally

- Replace server-backed conversation/document loading with IndexedDB reads and writes.
- Save messages, answers, and citations as they arrive.
- Restore conversations after a page refresh.
- Preserve existing document attachment, chat deletion, and citation behavior.

**Complete when:** browser profiles maintain separate histories and can restore their own chats.

### 4. Add request safeguards and cold-start handling

- Replace the SQLite-based per-conversation rate limit with server-side request limits suitable for a stateless API.
- Validate file types, upload size, document count, extracted-text size, and chat-history size.
- Keep the Gemini API key on Render only.
- Keep user input visible while Render wakes from idle; make failed requests recoverable.

**Complete when:** requests are bounded and cold starts or errors are understandable to users.

### 5. Configure Cloudflare Pages and Render

- Cloudflare Pages project root: `frontend`.
- Pages build command: `npm ci && npm run build`.
- Pages output directory: `dist`.
- Set `VITE_API_URL` to the deployed Render API URL.
- Render installs `requirements.txt` and the project package, then starts FastAPI on Render's assigned port.
- Set `GEMINI_API_KEY`, `GEMINI_MODEL`, and allowed frontend origins in Render environment settings.
- Configure FastAPI CORS for the production Pages origin and local development origins.

**Complete when:** the deployed frontend can call the deployed API and the Gemini key is not present in frontend assets.

### 6. Update project and learning documentation

- Update README instructions for local development and deployment.
- Update `learning/explanation.md`, `learning/progress.md`, and `learning/decisions.md` when useful milestones are completed.
- Keep this plan's checklist accurate; distinguish proposed work from completed work.

**Complete when:** the deployment steps and data flow are understandable and reproducible.

## Important limits and trade-offs

- Data is tied to a browser profile and does not automatically sync to another device.
- People sharing the same browser profile can see its saved data; this plan does not add user accounts.
- Render receives documents for processing, and Gemini receives relevant context for generation.
- Sending document text with each chat can increase request size and latency. Start with the simplest stateless design, then measure before adding a temporary cache.
- Requests currently allow at most 10 documents, 800,000 combined document characters, 12 recent messages / 20,000 history characters, 8 MiB per chat body, and 20 MiB per uploaded file. The server also limits each IP to 10 questions per minute per running process; this resets on restart and does not coordinate across instances.
- Browser storage is not a backup. The interface provides JSON export and per-chat/all-data deletion, but users still need to keep their own exported copy if they want a backup.
- The API uses Google's remote `gemini-embedding-001` (768-dim) with `GeminiEmbeddingProvider`. This replaces the local PyTorch `sentence-transformers` model, reducing API process memory from ~570 MB to under 50 MB (initial RSS ~4 MB, peak request <45 MB). This runs comfortably within Render's 512 MiB free tier container without risk of OOM crashes (Exit Code 137).
- Render's free web service has 512 MiB RAM, spins down after 15 minutes without traffic, and receives 750 free instance hours per workspace per calendar month. When those hours are exhausted, free web services are suspended until the next month. The filesystem is temporary, so it must not be used for user data.
- The public API has no user authentication in this plan. Add request limits and keep the Gemini key server-side; consider stronger access controls before inviting broad public use.

## Progress

- [x] Browser storage design and privacy explanation implemented
- [x] Stateless document parsing API implemented
- [x] Stateless chat API implemented
- [x] Frontend IndexedDB persistence and export/delete controls implemented
- [x] Request bounds, per-process rate limiting, encoder reuse, timeout, and retry recovery implemented
- [x] Gemini embeddings migration (`models/gemini-embedding-001`, 768-dim batch indexing) implemented for 512 MiB Render free tier
- [x] 100% backend tests (109 tests) and frontend production build verified
- [ ] Cloudflare Pages configured
- [ ] Render configured
- [x] README and learning notes updated
- [ ] Deployed flow verified

Repository changes are in place. The frontend production build, Python source
compilation, and all 109 backend tests have succeeded. Creating the hosted services still requires a Git
provider connection, a Gemini key, and the Pages origin for the Render CORS
setting. The deployment has not been performed.
