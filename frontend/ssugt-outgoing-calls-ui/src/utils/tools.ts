export function extractAndNormalizeFirstPhone(text: string): string | null {
  const match = text.match(/(\+?\d[\d\s\-\(\)]{6,}\d)/);
  if (!match) return null;

  const rawPhone = match[1];
  let digits = rawPhone.replace(/\D/g, "");

  if (digits.startsWith("8") && digits.length === 11) {
    digits = "7" + digits.slice(1);
  } else if (digits.startsWith("9") && digits.length === 10) {
    digits = "7" + digits;
  }

  if (digits.length < 7 || digits.length > 15) {
    return null;
  }

  return digits;
}
