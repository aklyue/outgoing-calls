import { useRef, useState } from "react";

export const useTemplateEditor = () => {
  const [textTemplate, setTextTemplate] = useState("");

  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [autocompletePos, setAutocompletePos] = useState({ top: 0, left: 0 });

  const [hovered, setHovered] = useState("");

  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const editorWrapRef = useRef<HTMLDivElement>(null);

  const insertToken = (token: string) => {
    const el = textAreaRef.current;
    if (!el) return;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    const newText =
      textTemplate.substring(0, start) + token + textTemplate.substring(end);
    setTextTemplate(newText);
    setShowAutocomplete(false);

    setTimeout(() => {
      el.focus();
      const newPos = start + token.length;
      el.setSelectionRange(newPos, newPos);
    }, 0);
  };

  const handleKeyDown = (e: React.KeyboardEvent<any>) => {
    if (e.key === "Escape") {
      setShowAutocomplete(false);
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const el = e.target;
    const val = el.value;
    const pos = el.selectionStart;

    setTextTemplate(val);

    if (val.charAt(pos - 1) === "[") {
      const elRect = el.getBoundingClientRect();
      const containerRect = editorWrapRef.current?.getBoundingClientRect();

      if (containerRect) {
        setAutocompletePos({
          top: elRect.bottom - containerRect.top,
          left: 10,
        });
        setShowAutocomplete(true);
        setHovered("__pause__");
      }
    }
    else if (showAutocomplete) {
      setShowAutocomplete(false);
    }
  };

  return {
    textTemplate,
    textAreaRef,
    editorWrapRef,
    showAutocomplete,
    autocompletePos,
    hovered,
    insertToken,
    handleInput,
    handleKeyDown,
  };
};
