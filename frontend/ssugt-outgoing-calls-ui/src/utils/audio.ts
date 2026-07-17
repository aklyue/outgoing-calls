export const resolvedText = (template: string, rows: any[]): string => {
  return template.replace(/\[([^\]]+)\]/g, (match, inner) => {
    const token = String(inner).trim();
    if (/^пауза\s+\d+$/i.test(token)) return match;
    return rows[0]?.[token] ?? "";
  });
};

export const arrayBufferFromAny = async (input: any): Promise<ArrayBuffer> => {
  if (typeof Blob !== "undefined" && input instanceof Blob) {
    return await input.arrayBuffer();
  }

  const isAnyBuffer =
    input instanceof ArrayBuffer ||
    (typeof SharedArrayBuffer !== "undefined" &&
      input instanceof SharedArrayBuffer);

  if (isAnyBuffer) {
    return input as ArrayBuffer;
  }

  if (ArrayBuffer.isView(input)) {
    return input.buffer.slice(
      input.byteOffset,
      input.byteOffset + input.byteLength,
    ) as ArrayBuffer;
  }

  if (typeof input === "string") {
    try {
      const b64 = input.includes(",") ? input.split(",").pop()! : input;
      const bin = atob(b64);
      const u8 = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) {
        u8[i] = bin.charCodeAt(i);
      }
      return u8.buffer as ArrayBuffer;
    } catch (e) {
      console.error("Failed to decode base64 string", e);
    }
  }

  return new Uint8Array(0).buffer as ArrayBuffer;
};

export function makeSilentWavBlob(durationMs = 60, sampleRate = 44100): Blob {
  const numCh = 1,
    bps = 16;
  const frameCount = Math.max(1, Math.round((durationMs / 1000) * sampleRate));
  const dataSize = frameCount * numCh * (bps / 8);
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);
  const writeStr = (v: DataView, off: number, s: string) => {
    for (let i = 0; i < s.length; i++) v.setUint8(off + i, s.charCodeAt(i));
  };
  writeStr(view, 0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeStr(view, 8, "WAVE");
  writeStr(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeStr(view, 36, "data");
  view.setUint32(40, dataSize, true);
  return new Blob([buffer], { type: "audio/wav" });
}
