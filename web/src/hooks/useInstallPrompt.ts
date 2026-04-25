import { useEffect, useState } from "react";
import { isIos, isStandalone } from "@/lib/utils";

export function useInstallPrompt() {
  const [standalone, setStandalone] = useState(isStandalone());
  const [ios] = useState(isIos());

  useEffect(() => {
    const mq = window.matchMedia("(display-mode: standalone)");
    const onChange = () => setStandalone(isStandalone());
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  return { standalone, ios, shouldPromptInstall: ios && !standalone };
}
