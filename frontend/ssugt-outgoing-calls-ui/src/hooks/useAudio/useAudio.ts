import { useEffect, useMemo, useRef, useState } from "react";
import type { Status } from "../../types/Status";
import {
  arrayBufferFromAny,
  makeSilentWavBlob,
  resolvedText,
} from "../../utils/audio";

interface UseAudioProps {
  template: string;
  rows: any[];
  col: string;
  ttsType: string;
  synthesize: (text: string, type: string) => Promise<any>;
}

export const useAudio = ({
  template,
  rows,
  col,
  ttsType,
  synthesize,
}: UseAudioProps) => {
  const [status, setStatus] = useState<Status>("idle");

  const mediaRef = useRef<HTMLAudioElement | null>(null);
  const warmedRef = useRef(false);
  const currentUrlRef = useRef<string | null>(null);
  const cacheRef = useRef<{ key: string; url: string } | null>(null);
  const playReqIdRef = useRef(0);
  const activeReqIdRef = useRef(0);

  const canPreview = useMemo(
    () => !!template && rows?.length > 0 && !!ttsType,
    [template, rows, ttsType],
  );

  const revoke = (url?: string | null) => {
    if (url) {
      try {
        URL.revokeObjectURL(url);
      } catch (e) {}
    }
  };

  const keyForCache = (): string =>
    `${ttsType}::${resolvedText(template, rows)}`;

  const warmup = async () => {
    if (warmedRef.current || !mediaRef.current) return;
    const el = mediaRef.current;
    const silentUrl = URL.createObjectURL(makeSilentWavBlob(60));
    try {
      el.muted = true;
      el.src = silentUrl;
      await el.play();
      await new Promise((r) => setTimeout(r, 80));
      el.pause();
      el.currentTime = 0;
      warmedRef.current = true;
    } catch (e) {
      console.warn("warmup failed:", e);
    } finally {
      revoke(silentUrl);
      el.muted = false;
    }
  };

  const getOrCreateUrl = async (): Promise<string> => {
    const key = keyForCache();
    if (cacheRef.current?.key === key && cacheRef.current.url) {
      return cacheRef.current.url;
    }

    const raw = await synthesize(resolvedText(template, rows), ttsType);
    const ab = await arrayBufferFromAny(raw);
    const blob = new Blob([ab], { type: "audio/wav" });
    const url = URL.createObjectURL(blob);

    if (cacheRef.current?.url && cacheRef.current.key !== key) {
      revoke(cacheRef.current.url);
    }
    cacheRef.current = { key, url };
    return url;
  };


  const stop = () => {
    activeReqIdRef.current = 0;
    const el = mediaRef.current;
    if (el) {
      try {
        el.pause();
      } catch {}
      try {
        el.currentTime = 0;
      } catch {}
    }
    setStatus("idle");
  };

  const onPlayStop = async () => {
    if (!canPreview || !mediaRef.current) return;

    if (status === "playing" || status === "loading") {
      stop();
      return;
    }

    const myId = ++playReqIdRef.current;
    activeReqIdRef.current = myId;
    setStatus("loading");

    try {
      await warmup();
      const url = await getOrCreateUrl();

      if (activeReqIdRef.current !== myId) return;

      const el = mediaRef.current;
      el.src = url;
      await el.play();

      currentUrlRef.current = url;
      setStatus("playing");

      el.onended = () => {
        setStatus((prev) => (prev === "playing" ? "idle" : prev));
      };
    } catch (e) {
      console.error("play error:", e);
      if (activeReqIdRef.current === myId) setStatus("idle");
    }
  };

  useEffect(() => {
    return () => {
      stop();
      revoke(currentUrlRef.current);
      if (cacheRef.current?.url) revoke(cacheRef.current.url);
    };
  }, []);

  return {
    status,
    onPlayStop,
    canPreview,
    mediaRef,
  };
};
