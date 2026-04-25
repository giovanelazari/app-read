import { useCallback, useState } from "react";
import BookCard from "@/components/BookCard";
import FocusModal from "@/components/FocusModal";
import { api, type BookWithCount, type FocusSession } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { formatDate } from "@/lib/utils";

export default function Library() {
  const booksFetcher = useCallback(() => api.books(), []);
  const { data: books, loading, error } = useApi<BookWithCount[]>(booksFetcher, [booksFetcher]);

  const focusFetcher = useCallback(() => api.focus(), []);
  const { data: focus, reload: reloadFocus } = useApi<FocusSession | null>(focusFetcher, [focusFetcher]);

  const [showFocusModal, setShowFocusModal] = useState(false);

  async function endFocus() {
    await api.endFocus();
    await reloadFocus();
  }

  if (loading) return <p className="text-ink-400">Carregando…</p>;
  if (error) return <p className="text-red-400">Erro: {error.message}</p>;

  return (
    <div className="space-y-4">
      {focus ? (
        <div className="card border-amber-500/50">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase text-amber-400">Foco ativo</div>
              <h3 className="font-serif text-lg">{focus.book.title}</h3>
              <p className="text-xs text-ink-400 mt-1">
                até {formatDate(focus.active_until)} · {focus.mode} · {focus.order_mode} · intensidade{" "}
                {focus.intensity}
              </p>
            </div>
            <button onClick={endFocus} className="btn-ghost-sm">
              Encerrar
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowFocusModal(true)}
          className="btn-primary w-full"
          disabled={!books || books.length === 0}
        >
          Ativar modo foco
        </button>
      )}

      <div className="space-y-3">
        {books?.map((b) => (
          <BookCard key={b.id} book={b} />
        ))}
        {books && books.length === 0 && (
          <div className="card text-ink-400">Nenhum livro ainda. Rode uma sincronização.</div>
        )}
      </div>

      {showFocusModal && books && (
        <FocusModal
          books={books}
          onClose={() => setShowFocusModal(false)}
          onCreated={async () => {
            setShowFocusModal(false);
            await reloadFocus();
          }}
        />
      )}
    </div>
  );
}
