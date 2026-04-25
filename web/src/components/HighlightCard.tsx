import { useState } from "react";
import { Link } from "react-router-dom";
import type { Highlight } from "@/lib/api";
import { api } from "@/lib/api";

type Props = {
  highlight: Highlight;
  onTagsChanged?: (hl: Highlight) => void;
  showBook?: boolean;
};

export default function HighlightCard({ highlight, onTagsChanged, showBook = true }: Props) {
  const [tagInput, setTagInput] = useState("");
  const [adding, setAdding] = useState(false);

  async function addTag() {
    const name = tagInput.trim().toLowerCase();
    if (!name) return;
    setAdding(true);
    try {
      const updated = await api.assignTags(highlight.id, [name]);
      setTagInput("");
      onTagsChanged?.(updated);
    } finally {
      setAdding(false);
    }
  }

  async function removeTag(tag: string) {
    const updated = await api.removeTag(highlight.id, tag);
    onTagsChanged?.(updated);
  }

  return (
    <article className="card">
      <p className="highlight-text">"{highlight.text}"</p>

      {showBook && (
        <div className="mt-4 text-sm text-ink-400">
          <Link
            to={`/books/${highlight.book.id}`}
            className="text-ink-200 hover:text-amber-400"
          >
            {highlight.book.title}
          </Link>
          {highlight.book.author && <> · {highlight.book.author}</>}
          {highlight.location && <> · {highlight.location}</>}
        </div>
      )}

      {highlight.note && (
        <div className="mt-3 text-sm text-ink-300 italic border-l-2 border-amber-500 pl-3">
          {highlight.note}
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {highlight.tags.map((t) => (
          <button
            key={t.id}
            onClick={() => removeTag(t.name)}
            className="text-xs px-2 py-1 rounded-full bg-ink-700 text-ink-200 hover:bg-red-900/40"
            title="Clique para remover"
          >
            #{t.name} ×
          </button>
        ))}
        <div className="flex items-center gap-1 ml-auto">
          <input
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addTag()}
            placeholder="+ tag"
            className="input py-1 text-sm w-24"
            disabled={adding}
          />
          <button onClick={addTag} disabled={adding} className="btn-ghost-sm">
            add
          </button>
        </div>
      </div>
    </article>
  );
}
