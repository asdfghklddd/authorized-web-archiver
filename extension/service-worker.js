import { isAllowedArchiveUrl, normalizeRecord } from "../lib/policy.js";

const HOST_NAME = "dev.andy.authorized_web_archiver";

const collectVisiblePage = () => ({
  url: window.location.href,
  title: document.title,
  text: document.body?.innerText ?? "",
});

const showBadge = async (tabId, text, color) => {
  await chrome.action.setBadgeBackgroundColor({ tabId, color });
  await chrome.action.setBadgeText({ tabId, text });
  setTimeout(() => chrome.action.setBadgeText({ tabId, text: "" }), 2200);
};

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id || !tab.url || !isAllowedArchiveUrl(tab.url)) {
    if (tab.id) await showBadge(tab.id, "DENY", "#9f2d2d");
    return;
  }

  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: collectVisiblePage,
    });
    const record = normalizeRecord(result);
    const response = await chrome.runtime.sendNativeMessage(HOST_NAME, record);
    if (!response?.ok) throw new Error("native host rejected the record");
    await showBadge(tab.id, "OK", "#176b52");
  } catch {
    await showBadge(tab.id, "ERR", "#9f2d2d");
  }
});
