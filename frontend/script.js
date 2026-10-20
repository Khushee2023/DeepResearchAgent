const $ = (id) => document.getElementById(id);
const form = $("query-form"), startBtn = $("start-btn"), approveBtn = $("approve-btn");
const planCard = $("plan-card"), planText = $("plan-text");
const progressCard = $("progress-card"), progressList = $("progress-list");
const errorCard = $("error-card"), reportCard = $("report-card"), reportEl = $("report");

const LABELS = {
  planner: "Planned sub-questions",
  approve_plan: "Plan approved",
  researcher: "Researched",
  critic: "Checked coverage",
  writer: "Wrote the report",
};

let source = null, threadId = null, originalPlan = [], reportMarkdown = "";

function resetUI() {
  [planCard, progressCard, errorCard, reportCard].forEach((el) => el.classList.add("hidden"));
  progressList.innerHTML = "";
  reportEl.innerHTML = "";
  reportMarkdown = "";
}

function addProgress(text) {
  progressCard.classList.remove("hidden");
  const li = document.createElement("li");
  li.textContent = text;
  progressList.appendChild(li);
}

function showError(msg) {
  errorCard.textContent = msg;
  errorCard.classList.remove("hidden");
}

function listen(url) {
  if (source) source.close();
  source = new EventSource(url);
  let finished = false;

  source.addEventListener("thread", (e) => { threadId = JSON.parse(e.data).thread_id; });

  source.addEventListener("progress", (e) => {
    const { node, detail } = JSON.parse(e.data);
    const label = LABELS[node] || node;
    addProgress(detail ? `${label}: ${detail}` : label);
  });

  source.addEventListener("plan", (e) => {
    const data = JSON.parse(e.data);
    threadId = data.thread_id;
    originalPlan = data.plan;
    planText.value = data.plan.join("\n");
    planCard.classList.remove("hidden");
    approveBtn.disabled = false;
  });

  source.addEventListener("report", (e) => {
    reportMarkdown = JSON.parse(e.data).report;
    reportEl.innerHTML = DOMPurify.sanitize(marked.parse(reportMarkdown));
    reportCard.classList.remove("hidden");
  });

  // 'error' naam EventSource ke apne connection-error event se milta hai:
  // server wala error event mein e.data hota hai, connection error mein nahi.
  source.addEventListener("error", (e) => {
    if (e.data) {
      showError(JSON.parse(e.data).message);
    } else if (!finished) {
      showError("Connection lost. Please try again.");
    }
    finished = true;
    source.close();
    startBtn.disabled = false;
  });

  // 'done' par band karna zaroori hai, warna EventSource khud reconnect karke run dobara chalata hai
  source.addEventListener("done", () => {
    finished = true;
    source.close();
    startBtn.disabled = false;
  });
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const query = $("query").value.trim();
  if (!query) return;
  resetUI();
  startBtn.disabled = true;
  listen(`/api/start?query=${encodeURIComponent(query)}`);
});

approveBtn.addEventListener("click", () => {
  const lines = planText.value.split("\n").map((l) => l.trim()).filter(Boolean);
  if (!lines.length || !threadId) return;
  const edited = JSON.stringify(lines) !== JSON.stringify(originalPlan);
  approveBtn.disabled = true;
  planCard.classList.add("hidden");
  startBtn.disabled = true;
  const url = `/api/resume/${threadId}` + (edited ? `?plan=${encodeURIComponent(JSON.stringify(lines))}` : "");
  listen(url);
});

$("copy-btn").addEventListener("click", () => {
  navigator.clipboard.writeText(reportMarkdown);
  $("copy-btn").textContent = "Copied!";
  setTimeout(() => ($("copy-btn").textContent = "Copy markdown"), 1500);
});