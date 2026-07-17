export const mapTemplateToCalls = (
  finalDf: any[],
  textTemplate: string,
  phoneColumn: string,
) => {
  return finalDf
    .map((r) => {
      const text = textTemplate.replace(/\[([^\]]+)\]/g, (match, inner) => {
        const token = inner.trim();
        if (/^пауза\s+\d+$/i.test(token)) return match;
        return r[token] ?? "";
      });
      return { phone_number: r[phoneColumn], text };
    })
    .filter((c) => c.phone_number && c.text);
};
