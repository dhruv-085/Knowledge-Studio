export type LocalRecord = {
  conversation_id: string;
  created_at: string;
  first_message: string | null;
  documents: unknown[];
  messages: unknown[];
};

const DATABASE_NAME = "leo-browser-data";
const STORE_NAME = "conversations";
const DATABASE_VERSION = 1;

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: "conversation_id" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("Could not open browser storage"));
  });
}

async function withStore<T>(
  mode: IDBTransactionMode,
  action: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, mode);
    const request = action(transaction.objectStore(STORE_NAME));
    let requestResult!: T;
    request.onsuccess = () => { requestResult = request.result; };
    request.onerror = () => reject(request.error ?? new Error("Browser storage request failed"));
    transaction.oncomplete = () => {
      database.close();
      resolve(requestResult);
    };
    transaction.onerror = () => {
      database.close();
      reject(transaction.error ?? new Error("Browser storage transaction failed"));
    };
    transaction.onabort = () => {
      database.close();
      reject(transaction.error ?? new Error("Browser storage transaction was cancelled"));
    };
  });
}

export const getAllConversations = () => withStore<LocalRecord[]>("readonly", (store) => store.getAll());
export const getConversation = (id: string) => withStore<LocalRecord | undefined>("readonly", (store) => store.get(id));
export const saveConversation = (record: LocalRecord) => withStore<IDBValidKey>("readwrite", (store) => store.put(record));
export const removeConversation = (id: string) => withStore<undefined>("readwrite", (store) => store.delete(id));
export const clearConversations = () => withStore<undefined>("readwrite", (store) => store.clear());
