// Common abbreviations whose trailing "." should NOT be treated as a sentence break.
// Keep this small and English-centric; missing entries just mean an extra (harmless) split.
const ABBREVIATIONS = new Set([
  "mr",
  "mrs",
  "ms",
  "dr",
  "sr",
  "jr",
  "st",
  "vs",
  "etc",
  "e.g",
  "i.e",
  "fig",
  "no",
  "vol",
  "approx",
  "inc",
  "ltd",
  "co",
]);

function isAbbreviation(prevWord: string): boolean {
  return ABBREVIATIONS.has(prevWord.toLowerCase().replace(/[^a-z.]/g, ""));
}

/**
 * Split arbitrary pasted text into individual sentences.
 *
 * Rules:
 * - Hard line breaks are always sentence breaks.
 * - Within a line, split after `.`, `!`, `?` (and runs thereof, plus optional
 *   trailing quote/bracket) when followed by whitespace + a capital/digit/quote.
 * - Common English abbreviations (Mr., Dr., e.g., etc.) don't trigger a split.
 *
 * Returned sentences are trimmed and never empty.
 */
export function splitIntoSentences(text: string): string[] {
  const normalized = text.replace(/\r\n?/g, "\n").trim();
  if (!normalized) return [];

  const out: string[] = [];
  const paragraphs = normalized.split(/\n+/);

  for (const paragraph of paragraphs) {
    const para = paragraph.trim();
    if (!para) continue;

    let start = 0;
    for (let i = 0; i < para.length; i++) {
      const ch = para[i];
      if (ch !== "." && ch !== "!" && ch !== "?") continue;

      // Consume runs of terminal punctuation (e.g. "...", "?!") and trailing closers.
      let end = i;
      while (end + 1 < para.length && /[.!?]/.test(para[end + 1])) end++;
      while (end + 1 < para.length && /["'”’)\]]/.test(para[end + 1])) end++;

      const next = para[end + 1];
      const isBoundary = next === undefined || /\s/.test(next);
      if (!isBoundary) {
        i = end;
        continue;
      }

      // Skip splits after abbreviations like "Dr." or "e.g.".
      if (ch === ".") {
        const prevWordMatch = para.slice(start, i).match(/([A-Za-z.]+)$/);
        if (prevWordMatch && isAbbreviation(prevWordMatch[1])) {
          i = end;
          continue;
        }
      }

      const sentence = para.slice(start, end + 1).trim();
      if (sentence) out.push(sentence);
      start = end + 1;
      i = end;
    }

    const tail = para.slice(start).trim();
    if (tail) out.push(tail);
  }

  return out;
}
