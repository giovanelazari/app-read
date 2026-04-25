import { useCallback, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import HighlightCard from "@/components/HighlightCard";
import { api, type Book, type Highlight } from "@/lib/api";
import { useApi } from "@/hooks/useApi";

export default function BookDetail() {
  const { id } = useParams();
  const bookId = Number(id);

  const bookFetcher = useCallback(() => api.book(bookId), [bookId]);
  const highlightsFetcher = useCallback(() => api.bookHighlights(bookId, 500), [bookId]);

  const { data: book, loading: bookLoading } = useApi<Book>(bookFetcher, [bookFetcher]);
  const { data: highlights, loading, error, setData } = useApi<Highlight[]>(
    highlightsFetcher,
    [highlightsFetcher],
  );

  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    if (!highlights) return [];
    if (!query) return highlights;
    const q = query.toLowerCase();
    return highlights.filter(
      (h) =>
        h.text.toLowerCase().includes(q) ||
        h.tags.some((t) => t.name.includes(q)) ||
        (h.note?.toLowerCase().includes(q) ?? false),
    );
  }, [highlights, query]);

  function updateHighlight(updated: Highlight) {
    if (!highlights) return;
    setData(highlights.map((h) => (h.id === updated.id ? updated : h)));
  }

  if (bookLoading || loading) return <p className="text-ink-400">Carregando…</p>;
  if (error) return <p className="text-red-400">Erro: {error.message}</p>;
  if (!book) return <p>Livro não encontrado.</p>;

  return (
    <div className="space-y-4">
      <Link to="/library" className="text-sm text-ink-400 hover:text-amber-400">
        ← Biblioteca
      </Link>
      <header className="card flex gap-3">
        {book.cover_url && (
          <img src={book.cover_url} alt="" className="w-20 h-28 object-cover rounded flex-shrink-0" />
        )}
        <div className="min-w-0">
          <h1 className="font-serif text-xl">{book.title}</h1>
          {book.author && <p className="text-sm text-ink-400">{book.author}</p>}
          <p className="text-xs text-ink-500 mt-2">
            {highlights?.length ?? 0} grifo{(highlights?.length ?? 0) === 1 ? "" : "s"}
          </p>
        </div>
      </header>

      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Buscar texto ou tag…"
        className="input"
      />

      <div className="space-y-3">
        {filtered.map((h) => (
          <HighlightCard
            key={h.id}
            highlight={h}
            showBook={false}
            onTagsChanged={updateHighlight}
          />
        ))}
        {filtered.length === 0 && <p className="text-ink-500">Nada encontrado.</p>}
      </div>
    </div>
  );
}
