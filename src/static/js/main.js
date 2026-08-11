async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const detail = data && data.detail ? data.detail : text;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function showStatus(el, message, isError = false) {
  if (!el) return;
  el.textContent = message;
  el.dataset.state = isError ? "error" : "ok";
}

document.addEventListener("DOMContentLoaded", () => {
  const generateForm = document.getElementById("generate-form");
  const parseForm = document.getElementById("parse-form");
  const status = document.getElementById("status");

  if (generateForm) {
    generateForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const prompt = new FormData(generateForm).get("prompt");
      showStatus(status, "Generating…");
      try {
        const result = await api("/resume/generate", {
          method: "POST",
          body: JSON.stringify({ prompt }),
        });
        sessionStorage.setItem("resumeId", result.id);
        sessionStorage.setItem("resume", JSON.stringify(result.resume));
        showStatus(status, `Saved resume ${result.id}`);
        window.location.href = `/resume?id=${result.id}`;
      } catch (err) {
        showStatus(status, err.message, true);
      }
    });
  }

  if (parseForm) {
    parseForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = new FormData(parseForm).get("text");
      showStatus(status, "Parsing…");
      try {
        const resume = await api("/resume/parse", {
          method: "POST",
          body: JSON.stringify({ text }),
        });
        const saved = await api("/resume", {
          method: "PUT",
          body: JSON.stringify(resume),
        });
        sessionStorage.setItem("resumeId", saved.id);
        sessionStorage.setItem("resume", JSON.stringify(saved.resume));
        showStatus(status, `Saved resume ${saved.id}`);
        window.location.href = `/resume?id=${saved.id}`;
      } catch (err) {
        showStatus(status, err.message, true);
      }
    });
  }

  const atsForm = document.getElementById("ats-form");
  if (atsForm) {
    atsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const resumeId = new URLSearchParams(window.location.search).get("id")
        || sessionStorage.getItem("resumeId");
      const jobDescription = new FormData(atsForm).get("job_description") || "";
      const out = document.getElementById("ats-result");
      if (!resumeId) {
        showStatus(out, "No resume id — create one on the home page first.", true);
        return;
      }
      showStatus(out, "Scoring…");
      try {
        const report = await api(`/resume/${resumeId}/ats`, {
          method: "POST",
          body: JSON.stringify({ job_description: jobDescription }),
        });
        out.textContent = JSON.stringify(report, null, 2);
        out.dataset.state = "ok";
      } catch (err) {
        showStatus(out, err.message, true);
      }
    });
  }
});
