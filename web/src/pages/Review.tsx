import { useCallback, useState } from "react";
import { api, type Highlight } from "@/lib/api";
import { useApi } from "@/hooks/useApi";

const EASE_OPTIONS = [
  { ease: 0, label: "Esqueci", desc: "não lembrava nada", color: "bg-red-600 hover:bg-red-500" },
  { ease: 3, label: "Difícil", desc: "lembrei com esforço", color: "bg-orange-600 hover:bg-orange-500" },
  { ease: 4, label: "OK", desc: "lembrei bem", color: "bg-green-600 hover:bg-green-500" },
  { ease: 5, label: "Fácil", desc: "lembrei imediatamente", color: "bg-amber-500 hover:bg-amber-400 text-ink-900" },
];

export default function Review() {
  const fetcher = useCallback(() => api.reviewQueue(20), []);
  const { data, loading, error, reload } = useApi<Highlight[]>(fetcher, [fetcher]);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function rate(ease: number) {
    if (!data || submitting) return;
    const current = data[index];
    setSubmitting(true);
    try {
      await api.review(current.id, ease);
      setRevealed(false);
      if (index + 1 >= data.length) {
        await reload();
        setIndex(0);
      } else {
        setIndex(index + 1);
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <p className="text-ink-400">Carregando…</p>;
  if (error) return <p className="text-red-400">Erro: {error.message}</p>;
  if (!data || data.length === 0) {
    return (
      <div className="card text-center">
        <h2 className="font-serif text-xl">Nada para revisar 🎉</h2>
        <p className="text-sm text-ink-400 mt-2">
          Volte mais tarde — o algoritmo vai trazer os grifos de volta na hora certa.
        </p>
      </div>
    );
  }

  const hl = data[index];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-xs text-ink-400">
        <span>
          {index + 1} / {data.length}
        </span>
        <span>SRS · SM-2</span>
      </div>

      <article className="card min-h-[200px]">
        <p className="highlight-text">"{hl.text}"</p>
        {revealed && (
          <div className="mt-4 text-sm text-ink-300 border-t border-ink-700 pt-3">
            <strong className="text-ink-100">{hl.book.title}</strong>
            {hl.book.author && <> · {hl.book.author}</>}
            {hl.location && <> · {hl.location}</>}
            {hl.note && (
              <div className="mt-2 italic border-l-2 border-amber-500 pl-3">{hl.note}</div>
            )}
          </div>
        )}
      </article>

      {!revealed ? (
        <button onClick={() => setRevealed(true)} className="btn-primary w-full">
          Mostrar contexto
        </button>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          {EASE_OPTIONS.map((opt) => (
            <button
              key={opt.ease}
              onClick={() => rate(opt.ease)}
              disabled={submitting}
              className={`${opt.color} text-white rounded-lg py-3 text-left px-4 disabled:opacity-50`}
            >
              <div className="font-semibold">{opt.label}</div>
              <div className="text-xs opacity-80">{opt.desc}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
