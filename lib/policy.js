export const ALLOWED_ORIGIN = "http://127.0.0.1:8787";
export const MAX_TEXT_CHARS = 100_000;
const SAFE_TITLE = /^[^\u0000-\u001f\u007f]{1,200}$/u;

export const isAllowedArchiveUrl = (input) => {
  try {
    const url = new URL(input);
    return (
      url.origin === ALLOWED_ORIGIN &&
      url.username === "" &&
      url.password === "" &&
      url.protocol === "http:"
    );
  } catch {
    return false;
  }
};

export const normalizeRecord = (candidate) => {
  if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) {
    throw new TypeError("record must be an object");
  }
  const { url, title, text } = candidate;
  if (typeof url !== "string" || !isAllowedArchiveUrl(url)) {
    throw new TypeError("URL is outside the exact localhost allowlist");
  }
  if (typeof title !== "string" || !SAFE_TITLE.test(title.trim())) {
    throw new TypeError("title is invalid");
  }
  if (typeof text !== "string" || text.length === 0) {
    throw new TypeError("page text is invalid");
  }
  const normalizedText = text.replace(/\r\n?/g, "\n").trim().slice(0, MAX_TEXT_CHARS);
  if (!normalizedText) throw new TypeError("page text is empty");
  return Object.freeze({
    version: 1,
    url: new URL(url).href,
    title: title.trim(),
    text: normalizedText,
    captured_at: new Date().toISOString(),
  });
};
