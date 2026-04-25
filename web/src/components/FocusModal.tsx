import { useState } from "react";
import { api, type BookWithCount } from "@/lib/api";

type Props = {
  books: BookWithCount[];
  onClose: () => void;
  onCreated: () => void | Promise<void>;
};

export default function FocusModal({ books, onClose, onCreated }: Props) {
  const [bookId, setBookId] = useState<number>(books[0]?.id ?? 0);
  const [days, setDays] = useState(7);
  const [intensity, setIntensity] = useState(3);
  const [mode, setMode] = useState<"replace" | "augment">("augment");
  const [orderMode, setOrderMode] = useState<"sequential" | "random">("sequential");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    setSubmitting(true);
    try {
      await api.createFocus({ book_id: bookId, days, intensity, mode, order_mode: orderMode });
      await onCreated();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/70 z-30 flex items-end sm:items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="card w-full max-w-md space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="font-serif text-xl">Ativar foco</h2>

        <label className="block space-y-1">
          <span className="text-sm text-ink-400">Livro</span>
          <select
            value={bookId}
            onChange={(e) => setBookId(Number(e.target.value))}
            className="input"
          >
            {books.map((b) => (
              <option key={b.id} value={b.id}>
                {b.title}
              </option>
            ))}
          </select>
        </label>

        <label className="block space-y-1">
          <span className="text-sm text-ink-400">Dias: {days}</span>
          <input
            type="range"
            min={1}
            max={30}
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="w-full"
          />
        </label>

        <label className="block space-y-1">
          <span className="text-sm text-ink-400">Intensidade: {intensity} / 5</span>
          <input
            type="range"
            min={1}
            max={5}
            value={intensity}
            onChange={(e) => setIntensity(Number(e.target.value))}
            className="w-full"
          />
        </label>

        <fieldset className="space-y-1">
          <span className="text-sm text-ink-400">Modo</span>
          <div className="grid grid-cols-2 gap-2">
            {(["replace", "augment"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`btn ${mode === m ? "bg-amber-500 text-ink-900" : "bg-ink-700"}`}
              >
                {m === "replace" ? "Só esse livro" : "Prioriza esse livro"}
              </button>
            ))}
          </div>
        </fieldset>

        <fieldset className="space-y-1">
          <span className="text-sm text-ink-400">Ordem</span>
          <div className="grid grid-cols-2 gap-2">
            {(["sequential", "random"] as const).map((o) => (
              <button
                key={o}
                type="button"
                onClick={() => setOrderMode(o)}
                className={`btn ${orderMode === o ? "bg-amber-500 text-ink-900" : "bg-ink-700"}`}
              >
                {o === "sequential" ? "Sequencial" : "Aleatória"}
              </button>
            ))}
          </div>
        </fieldset>

        <div className="flex gap-2 justify-end pt-2">
          <button onClick={onClose} className="btn-ghost">
            Cancelar
          </button>
          <button onClick={submit} disabled={submitting || !bookId} className="btn-primary">
            Ativar
          </button>
        </div>
      </div>
    </div>
  );
}
