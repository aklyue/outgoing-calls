import { useEffect, useState } from "react";
import { ttsDescriptionMap } from "../../const/ttsDescriptionMap";

export const useTts = ({
  open,
  getSynthesizers,
}: {
  open: boolean;
  getSynthesizers: () => Promise<string[]>;
}) => {
  const [ttsOptions, setTtsOptions] = useState<string[]>([]);
  const [ttsType, setTtsType] = useState("");
  const [ttsLoading, setTtsLoading] = useState(false);

  useEffect(() => {
    if (open) {
      (async () => {
        setTtsLoading(true);
        try {
          const list = await getSynthesizers();
          setTtsOptions(list);
          if (list.length) setTtsType(list[0]);
        } finally {
          setTtsLoading(false);
        }
      })();
    }
  }, [open]);

  const ttsExtraText = ttsType
    ? ttsDescriptionMap[ttsType] ||
      "Этот движок будет использоваться для озвучки текста."
    : "Выберите сервис синтеза речи.";

  return {
    ttsOptions,
    ttsType,
    setTtsType,
    ttsLoading,
    ttsExtraText,
  };
};
