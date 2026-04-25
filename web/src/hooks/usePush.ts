import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { arrayBufferToBase64, urlBase64ToUint8Array } from "@/lib/utils";

type PushState = "unsupported" | "denied" | "granted" | "default" | "pending";

export function usePush() {
  const [state, setState] = useState<PushState>("pending");
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);

  const refresh = useCallback(async () => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator) || !("PushManager" in window)) {
      setState("unsupported");
      return;
    }
    const perm = Notification.permission;
    if (perm === "denied") {
      setState("denied");
      return;
    }
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    setSubscription(sub);
    setState(perm === "granted" && sub ? "granted" : perm);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const subscribe = useCallback(async () => {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;
    // Notification.requestPermission must be invoked from a user gesture — this function
    // is only called from a click handler (see PushPrompt.tsx).
    const perm = await Notification.requestPermission();
    if (perm !== "granted") {
      setState(perm === "denied" ? "denied" : "default");
      return;
    }
    const reg = await navigator.serviceWorker.ready;
    const { public_key } = await api.vapidKey();
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(public_key),
    });
    await api.subscribePush({
      endpoint: sub.endpoint,
      keys: {
        p256dh: arrayBufferToBase64(sub.getKey("p256dh")),
        auth: arrayBufferToBase64(sub.getKey("auth")),
      },
      user_agent: navigator.userAgent,
    });
    setSubscription(sub);
    setState("granted");
  }, []);

  const unsubscribe = useCallback(async () => {
    if (!subscription) return;
    try {
      await api.unsubscribePush(subscription.endpoint);
    } catch {
      /* non-fatal: the endpoint may already be stale on the server */
    }
    await subscription.unsubscribe();
    setSubscription(null);
    setState("default");
  }, [subscription]);

  return { state, subscription, subscribe, unsubscribe, refresh };
}
