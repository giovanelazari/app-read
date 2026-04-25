import { useCallback, useState } from "react";
import { useSearchParams } from "react-router-dom";
import HighlightCard from "@/components/HighlightCard";
import { api, type Highlight } from "@/lib/api";
import { useApi } from "@/hooks/useApi";

export default function Home() {
  const [params] = useSearchParams();
  const highlightId = params.get("highlight");

  const fetcher = useCallback(() => {
    if (highlightId) {
      // Just use today endpoint; deep-link via /books/:id is a better UX for a specific highlight.
      // We keep it simple: if highlight param exists, still show today's pick.
    }
    return api.today();
  }, [highlightId]);

  const { data, loading, error, reload, setData } = useApi<Highlight>(fetcher, [fetcher]);
  const [shufflingNext, setShufflingNext] = useState(false);

  async function next() {
    setShufflingNext(true);
    try {
      const hl = await api.random();
      setData(hl);
    } finally {
      setShufflingNext(false);
    }
  }

  if (loading) return <p className="text-ink-400">Carregando…</p>;
  if (error) {
    return (
      <div className="card">
        <p className="text-red-400">Erro: {error.message}</p>
        <button onClick={reload} className="mt-3 btn-ghost">
          Tentar novamente
        </button>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="card">
        <p className="text-ink-300">Nenhum grifo ainda. Rode uma sincronização em Configurações.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <HighlightCard highlight={data} onTagsChanged={setData} />
      <div className="flex gap-2">
        <button onClick={next} disabled={shufflingNext} className="btn-primary flex-1">
          Próximo
        </button>
      </div>
    </div>
  );
}
