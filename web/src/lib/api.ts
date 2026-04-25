const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type Tag = { id: number; name: string };
export type TagCount = Tag & { count: number };
export type Book = {
  id: number;
  asin: string;
  title: string;
  author: string | null;
  cover_url: string | null;
  last_synced: string | null;
};
export type BookWithCount = Book & { highlights_count: number };
export type Highlight = {
  id: number;
  book_id: number;
  text: string;
  location: string | null;
  color: string | null;
  note: string | null;
  highlighted_at: string | null;
  created_at: string;
  book: Book;
  tags: Tag[];
};
export type FocusSession = {
  id: number;
  book_id: number;
  active_until: string;
  intensity: number;
  mode: "replace" | "augment";
  order_mode: "sequential" | "random";
  cursor: number;
  book: Book;
};
export type SyncStatus = {
  id: number | null;
  started_at: string | null;
  finished_at: string | null;
  status: string | null;
  books_added: number;
  highlights_added: number;
  error_message: string | null;
  running: boolean;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  // highlights
  today: () => request<Highlight>("/highlights/today"),
  random: () => request<Highlight>("/highlights/random"),
  reviewQueue: (limit = 10) =>
    request<Highlight[]>(`/highlights/review-queue?limit=${limit}`),
  review: (id: number, ease: number) =>
    request<{
      highlight_id: number;
      ef: number;
      interval_days: number;
      reps: number;
      next_review_at: string;
    }>(`/highlights/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ ease }),
    }),
  byTag: (tag: string, limit = 50, offset = 0) =>
    request<Highlight[]>(
      `/highlights/by-tag/${encodeURIComponent(tag)}?limit=${limit}&offset=${offset}`,
    ),
  assignTags: (id: number, tags: string[]) =>
    request<Highlight>(`/highlights/${id}/tags`, {
      method: "POST",
      body: JSON.stringify({ tags }),
    }),
  removeTag: (id: number, tag: string) =>
    request<Highlight>(
      `/highlights/${id}/tags/${encodeURIComponent(tag)}`,
      { method: "DELETE" },
    ),

  // books
  books: () => request<BookWithCount[]>("/books"),
  book: (id: number) => request<Book>(`/books/${id}`),
  bookHighlights: (id: number, limit = 100, offset = 0) =>
    request<Highlight[]>(
      `/books/${id}/highlights?limit=${limit}&offset=${offset}`,
    ),

  // review stats
  reviewStats: () => request<{ due: number; total: number }>("/review/stats"),

  // focus
  focus: () => request<FocusSession | null>("/focus"),
  createFocus: (body: {
    book_id: number;
    days: number;
    intensity: number;
    mode: "replace" | "augment";
    order_mode: "sequential" | "random";
  }) => request<FocusSession>("/focus", { method: "POST", body: JSON.stringify(body) }),
  endFocus: () => request<void>("/focus", { method: "DELETE" }),

  // tags
  tags: () => request<TagCount[]>("/tags"),
  createTag: (name: string) =>
    request<Tag>("/tags", { method: "POST", body: JSON.stringify({ name }) }),

  // push
  vapidKey: () => request<{ public_key: string }>("/push/vapid-public-key"),
  subscribePush: (sub: {
    endpoint: string;
    keys: { p256dh: string; auth: string };
    user_agent?: string;
  }) => request<{ status: string }>("/push/subscribe", {
    method: "POST",
    body: JSON.stringify(sub),
  }),
  unsubscribePush: (endpoint: string) =>
    request<void>("/push/subscribe", {
      method: "DELETE",
      body: JSON.stringify({ endpoint }),
    }),

  // sync
  triggerSync: () =>
    request<{ status: string }>("/sync", { method: "POST" }),
  syncStatus: () => request<SyncStatus>("/sync/status"),
};
