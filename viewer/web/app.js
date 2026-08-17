const recordsNode = document.getElementById("records");
const detailNode = document.getElementById("detail");

const element = (name, text, className) => {
  const node = document.createElement(name);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};

const showDetail = async (recordId) => {
  const response = await fetch(`/api/records/${encodeURIComponent(String(recordId))}`, {
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("Record could not be loaded");
  const record = await response.json();
  detailNode.replaceChildren(
    element("p", new Date(record.captured_at).toLocaleString(), "eyebrow"),
    element("h2", record.title),
    element("p", record.url, "source"),
    element("pre", record.body_text),
    element("code", `SHA-256 ${record.record_sha256}`),
  );
};

const load = async () => {
  const response = await fetch("/api/records", {
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("Archive could not be loaded");
  const { records } = await response.json();
  const items = records.map((record) => {
    const button = element("button");
    button.type = "button";
    button.append(element("strong", record.title), element("span", record.excerpt));
    button.addEventListener("click", () => showDetail(record.record_id).catch(showError));
    const item = element("li");
    item.append(button);
    return item;
  });
  recordsNode.replaceChildren(...items);
};

const showError = () => {
  detailNode.replaceChildren(element("p", "The local archive is unavailable."));
};

load().catch(showError);
