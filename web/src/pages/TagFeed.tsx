import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import HighlightCard from "@/components/HighlightCard";
import { api, type Highlight } from "@/lib/api";
import { useApi } from "@/hooks/useApi";

export default function TagFeed() {
  const { name = "" } = useParams();
  const fetcher = useCallback(() => api.byTag(name, 200), [name]);
  const { data, loading, error, setData } = useApi<Highlight[]>(fetcher, [fetcher]);

  function updateHighlight(updated: Highlight) {
    if (!data) return;
    setData(data.map((h) => (h.id === updated.id ? updated : h)));
  }

  if (loading) return <p className="text-ink-400">Carregando…</p>;
  if (error) return <p className="text-red-400">Erro: {error.message}</p>;

  return (
    <div className="space-y-4">
      <Link to="/tags" className="text-sm text-ink-400 hover:text-amber-400">
        ← Tags
      </Link>
      <h1 className="font-serif text-2xl">#{name}</h1>
      <p className="text-xs text-ink-500">{data?.length ?? 0} grifos</p>
      <div className="space-y-3">
        {data?.map((h) => (
          <HighlightCard key={h.id} highlight={h} onTagsChanged={updateHighlight} />
        ))}
      </div>
    </div>
  );
}
