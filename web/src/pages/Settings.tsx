import { useCallback, useState } from "react";
import PushPrompt from "@/components/PushPrompt";
import { api, type SyncStatus } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { formatDate } from "@/lib/utils";

export default function Settings() {
  const fetcher = useCallback(() => api.syncStatus(), []);
  const { data, reload } = useApi<SyncStatus>(fetcher, [fetcher]);
  const [triggering, setTriggering] = useState(false);

  async function trigger() {
    setTriggering(true);
    try {
      await api.triggerSync();
      // Give the background task a moment to flip the running flag.
      setTimeout(reload, 1000);
    } finally {
      setTriggering(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="font-serif text-2xl">Configurações</h1>

      <PushPrompt />

      <section className="card">
        <h3 className="font-semibold">Sincronização Kindle</h3>
        {data && (
          <dl className="mt-2 text-sm text-ink-400 space-y-1">
            <div className="flex justify-between">
              <dt>Último status:</dt>
              <dd className="text-ink-200">{data.status || "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Último run:</dt>
              <dd className="text-ink-200">{formatDate(data.started_at)}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Livros novos:</dt>
              <dd className="text-ink-200">{data.books_added}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Grifos novos:</dt>
              <dd className="text-ink-200">{data.highlights_added}</dd>
            </div>
            {data.error_message && (
              <div className="text-red-400 pt-2">{data.error_message}</div>
            )}
          </dl>
        )}
        <div className="mt-3 flex gap-2">
          <button
            onClick={trigger}
            disabled={triggering || data?.running}
            className="btn-primary"
          >
            {data?.running ? "Sincronizando…" : "Sincronizar agora"}
          </button>
          <button onClick={reload} className="btn-ghost">
            Atualizar
          </button>
        </div>
      </section>

      <section className="card">
        <h3 className="font-semibold">Renovar login Amazon</h3>
        <p className="text-sm text-ink-400 mt-2">
          Quando o status aparecer como <code>auth_required</code>, rode localmente:
        </p>
        <pre className="mt-2 bg-ink-900 border border-ink-700 rounded p-3 text-xs overflow-x-auto">
{`cd api
HEADED=1 python -m app.scraper.run`}
        </pre>
        <p className="text-sm text-ink-400 mt-2">
          Faça login + 2FA no navegador que abrir, depois suba <code>data/playwright/</code> para o VPS.
        </p>
      </section>
    </div>
  );
}
