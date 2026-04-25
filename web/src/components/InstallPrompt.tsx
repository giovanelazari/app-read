import { useState } from "react";
import { useInstallPrompt } from "@/hooks/useInstallPrompt";

export default function InstallPrompt() {
  const { shouldPromptInstall } = useInstallPrompt();
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem("installPromptDismissed") === "1",
  );

  if (!shouldPromptInstall || dismissed) return null;

  return (
    <div className="mb-4 card border-amber-500/50 bg-amber-500/10">
      <h3 className="font-semibold text-amber-300">Instale o app</h3>
      <p className="text-sm text-ink-200 mt-1">
        Para receber notificações, toque em{" "}
        <span className="font-mono">Compartilhar</span> →{" "}
        <span className="font-mono">Adicionar à Tela Inicial</span>, depois abra pelo ícone.
      </p>
      <button
        onClick={() => {
          localStorage.setItem("installPromptDismissed", "1");
          setDismissed(true);
        }}
        className="mt-3 btn-ghost-sm"
      >
        Entendi
      </button>
    </div>
  );
}
