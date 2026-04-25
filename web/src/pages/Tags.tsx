import { useCallback } from "react";
import { Link } from "react-router-dom";
import { api, type TagCount } from "@/lib/api";
import { useApi } from "@/hooks/useApi";

export default function Tags() {
  const fetcher = useCallback(() => api.tags(), []);
  const { data, loading, error } = useApi<TagCount[]>(fetcher, [fetcher]);

  if (loading) return <p className="text-ink-400">Carregando…</p>;
  if (error) return <p className="text-red-400">Erro: {error.message}</p>;

  return (
    <div className="space-y-3">
      <h1 className="font-serif text-2xl">Tags</h1>
      {data && data.length === 0 && (
        <p className="text-ink-500">Nenhuma tag ainda. Tagueie grifos pela home ou detalhe do livro.</p>
      )}
      <div className="flex flex-wrap gap-2">
        {data?.map((t) => (
          <Link
            key={t.id}
            to={`/tags/${encodeURIComponent(t.name)}`}
            className="px-3 py-2 rounded-full bg-ink-800 border border-ink-700 hover:border-amber-500"
          >
            <span>#{t.name}</span>
            <span className="ml-2 text-xs text-ink-400">{t.count}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
