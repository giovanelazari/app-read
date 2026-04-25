import { usePush } from "@/hooks/usePush";
import { useInstallPrompt } from "@/hooks/useInstallPrompt";

export default function PushPrompt() {
  const { state, subscribe, unsubscribe } = usePush();
  const { standalone, ios } = useInstallPrompt();

  if (state === "unsupported") {
    return (
      <div className="card">
        <h3 className="font-semibold">Notificações</h3>
        <p className="text-sm text-ink-400 mt-1">
          Este navegador não suporta push. Tente Safari (iOS 16.4+) ou Chrome.
        </p>
      </div>
    );
  }

  if (ios && !standalone) {
    return (
      <div className="card">
        <h3 className="font-semibold">Notificações</h3>
        <p className="text-sm text-ink-400 mt-1">
          No iOS, push só funciona após adicionar o app à tela inicial. Faça isso primeiro.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="font-semibold">Notificações</h3>
      <p className="text-sm text-ink-400 mt-1">
        Estado:{" "}
        <span className="text-ink-200">
          {state === "granted"
            ? "ativas"
            : state === "denied"
            ? "negadas (ajuste nas configurações do navegador)"
            : "inativas"}
        </span>
      </p>
      <div className="mt-3 flex gap-2">
        {state !== "granted" && (
          <button onClick={subscribe} className="btn-primary" disabled={state === "denied"}>
            Ativar notificações
          </button>
        )}
        {state === "granted" && (
          <button onClick={unsubscribe} className="btn-ghost">
            Desativar
          </button>
        )}
      </div>
    </div>
  );
}
