document.addEventListener("DOMContentLoaded", () => {
  const questionsBtn = document.querySelector(".nav-buttons button:nth-child(1)");
  const answersBtn   = document.querySelector(".nav-buttons button:nth-child(2)");
  const testBtn      = document.querySelector(".nav-buttons button:nth-child(3)");
  const sendBtn      = document.querySelector(".nav-buttons button:nth-child(4)");
  const questionBox  = document.getElementById("questions-box");

  const API_BASE = "http://127.0.0.1:5000";

  let currentQuestions = [];
  let currentModelApi = "template";
  let currentTipApi = "strategie optima";

  const allowedTips = new Set(["minmax", "asignari", "echilibru nash", "strategie optima", "mix"]);
  const allowedModels = new Set(["template", "optim-mode", "alphabeta"]);

  const mapModel = (raw) => {
    const m = String(raw || "").trim().toLowerCase();
    if (allowedModels.has(m)) return m;
    if (m.includes("template")) return "template";
    if (m.includes("optim")) return "optim-mode";
    if (m.includes("alpha") || m.includes("beta")) return "alphabeta";
    return "template";
  };

  const mapTip = (v) => {
    const t = String(v || "").trim().toLowerCase();
    if (!t) return "strategie optima";
    if (t.includes("mix") || t.includes("all") || t.includes("toate") || t.includes("test")) return "mix";
    if (t.includes("minmax") || t.includes("minimax") || t.includes("alpha") || t.includes("beta")) return "minmax";
    if (t.includes("asign") || t.includes("csp")) return "asignari";
    if (t.includes("nash") || t.includes("echilibru")) return "echilibru nash";
    if (t.includes("search")) return "search";
    if (t.includes("bayes")) return "bayes";
    return "strategie optima";
  };

  function getSelect(name) {
    const el = document.querySelector(`select[name="${name}"]`);
    if (!el) throw new Error(`Nu găsesc <select name="${name}"> în HTML.`);
    return el;
  }

  function getSelectedRaw(selectEl) {
    const val = String(selectEl.value || "").trim();
    const txt = String(selectEl.options?.[selectEl.selectedIndex]?.text || "").trim();
    return { val, txt };
  }

  async function fetchJson(url, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    console.log("FETCH:", method, url);

    const headers = { ...(options.headers || {}) };

    let body = options.body;
    if (body && typeof body === "object" && !(body instanceof FormData)) {
      headers["Content-Type"] = headers["Content-Type"] || "application/json";
      body = JSON.stringify(body);
    }

    const res = await fetch(url, { ...options, method, headers, body });
    const text = await res.text();

    if (!res.ok) {
      console.error("HTTP", res.status, text);
      throw new Error(`HTTP ${res.status}: ${text.slice(0, 400)}`);
    }

    try {
      return JSON.parse(text);
    } catch {
      console.error("Răspuns non-JSON:", text);
      throw new Error("Backend a răspuns non-JSON (vezi consola).");
    }
  }

  const placeholderForType = (type) => {
    const t = String(type || "").toLowerCase();
    if (t === "minmax") return "Ex: 5 6 (valoare frunze)";
    if (t === "asignari") return "Ex: X=1, Y=2 (sau 'nu există soluție')";
    if (t === "nash") return "Ex: DA. Echilibre: [(0,0)] / NU";
    if (t === "optima") return "Scrie strategia optimă...";
    return "Scrie răspunsul tău aici...";
  };

  questionsBtn?.addEventListener("click", () => (window.location.href = "Ask.html"));

  let answersVisible = false;
  answersBtn?.addEventListener("click", () => {
    answersVisible = !answersVisible;
    document.querySelectorAll(".answer").forEach(a => (a.style.display = answersVisible ? "block" : "none"));
  });

  // ✅ TEST = MIX (10 întrebări din toate tipurile)
  testBtn?.addEventListener("click", async () => {
    try {
      const modelSel = getSelect("metod");
      const { val: modelVal, txt: modelTxt } = getSelectedRaw(modelSel);

      currentModelApi = mapModel(allowedModels.has(modelVal.toLowerCase()) ? modelVal : modelTxt);
      currentTipApi = "mix";

      const url = `${API_BASE}/smartest/test?tip=mix&model=${encodeURIComponent(currentModelApi)}`;
      const data = await fetchJson(url);

      currentQuestions = data.questions || [];
      renderQuestions(currentQuestions, currentTipApi);
    } catch (err) {
      console.error(err);
      questionBox.innerHTML = `<p style="color:red;">${String(err.message || err)}</p>`;
    }
  });

  // ✅ TRIMITE = filtrat după selecție
  sendBtn?.addEventListener("click", async () => {
    try {
      const countSel = getSelect("numar-intrebari");
      const tipSel = getSelect("Tipul De Intrebare");
      const modelSel = getSelect("metod");

      const { val: countVal } = getSelectedRaw(countSel);
      const { val: tipVal, txt: tipTxt } = getSelectedRaw(tipSel);
      const { val: modelVal, txt: modelTxt } = getSelectedRaw(modelSel);

      const count = parseInt(countVal, 10);
      if (!count || count < 1) throw new Error("Numărul de întrebări e invalid.");

      currentTipApi = mapTip(allowedTips.has(tipVal.toLowerCase()) ? tipVal : tipTxt);
      currentModelApi = mapModel(allowedModels.has(modelVal.toLowerCase()) ? modelVal : modelTxt);

      const url =
        `${API_BASE}/smartest/question?count=${encodeURIComponent(count)}` +
        `&model=${encodeURIComponent(currentModelApi)}&tip=${encodeURIComponent(currentTipApi)}`;

      const data = await fetchJson(url);

      currentQuestions = data.questions || [];
      renderQuestions(currentQuestions, currentTipApi);
    } catch (err) {
      console.error(err);
      questionBox.innerHTML = `<p style="color:red;">${String(err.message || err)}</p>`;
    }
  });

  function renderQuestions(list, tipApi) {
    questionBox.innerHTML = "";
    if (!list || list.length === 0) {
      questionBox.innerHTML = "<p>Nicio întrebare găsită.</p>";
      return;
    }

    list.forEach((q, index) => {
      const div = document.createElement("div");
      div.classList.add("question-item");

      const ph =
        tipApi === "mix"
          ? placeholderForType(q.type)
          : placeholderForType(tipApi === "echilibru nash" ? "nash" : tipApi);

      const safeQ = String(q.text ?? "").replaceAll("\n", "<br>");
      const safeA = String(q.answer ?? "").replaceAll("\n", "<br>");

      div.innerHTML = `
        <p class="q-text"><strong>${index + 1}.</strong> ${safeQ}</p>
        <input type="text" class="user-answer" placeholder="${ph}">
        <p class="answer" style="display:none;">${safeA}</p>
      `;
      questionBox.appendChild(div);
    });

    const verifyBtn = document.createElement("button");
    verifyBtn.textContent = "Verifică răspunsurile";
    verifyBtn.classList.add("verify-btn");
    verifyBtn.type = "button"; // IMPORTANT dacă ești în <form>
    questionBox.appendChild(verifyBtn);

    const result = document.createElement("p");
    result.id = "score-result";
    result.style.textAlign = "center";
    questionBox.appendChild(result);

    verifyBtn.addEventListener("click", async (e) => {
      e.preventDefault();

      try {
        const inputs = Array.from(document.querySelectorAll(".user-answer"));

        const userAnswers = list.map((q, i) => ({
          id: q.id,
          type: q.type,
          game_id: q.game_id ?? null,
          question: q.text ?? "",
          user_answer: inputs[i]?.value?.trim() || ""
        }));

        const verifyUrl =
          `${API_BASE}/smartest/raspunsuri?model=${encodeURIComponent(currentModelApi)}` +
          `&tip=${encodeURIComponent(currentTipApi)}`;

        const data = await fetchJson(verifyUrl, {
          method: "POST",
          body: { answers: userAnswers }
        });

        result.textContent = `Scorul tău: ${data.score}%`;
      } catch (err) {
        console.error(err);
        result.textContent = `Eroare la verificare: ${String(err?.message || err)}`;
      }
    });
  }
});
