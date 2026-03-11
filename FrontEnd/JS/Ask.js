document.addEventListener("DOMContentLoaded", () => {
  const API_BASE = "http://127.0.0.1:5000";

  const backBtn = document.querySelector(".nav-buttons button");
  const askBtn = document.getElementById("ask-btn");
  const questionInput = document.getElementById("user-question");
  const modelSelect = document.querySelector('select[name="model"]');
  const tipSelect = document.querySelector('select[name="tip"]');
  const answerBox = document.getElementById("answer-box");

  const minmaxHint = document.getElementById("minmax-hint");

  backBtn.addEventListener("click", () => {
    window.location.href = "MainPage.html";
  });

  const mapModel = (v) => {
    const m = (v || "").trim().toLowerCase();
    if (m === "template") return "template";
    if (m === "optim-mode" || m === "optim mode" || m === "ml" || m === "rn") return "optim-mode";
    if (m.includes("alpha")) return "alphabeta";
    return "template";
  };

  const mapTip = (v) => {
    const t = (v || "").trim().toLowerCase();
    if (t.includes("minmax")) return "minmax";
    if (t.includes("asign")) return "asignari";
    if (t.includes("nash")) return "echilibru nash";
    return "strategie optima";
  };

  function syncUI() {
    const tip = mapTip(tipSelect?.value || "");
    const model = mapModel(modelSelect?.value || "");

    if (tip === "minmax") {
      minmaxHint.style.display = "block";

      if (!questionInput.value.trim()) {
        questionInput.placeholder = "Ex: MAX(MIN(3,5),MIN(2,9))";
      }
      if (modelSelect && modelSelect.selectedIndex > 0 && model !== "alphabeta") {
        // Nu forțăm, dar sugerăm implicit AlphaBeta.
        // (dacă vrei forțare, zi și îl setez automat)
      }
    } else {
      minmaxHint.style.display = "none";
      questionInput.placeholder = "Scrie aici întrebarea ta...";
    }
  }

  tipSelect?.addEventListener("change", syncUI);
  modelSelect?.addEventListener("change", syncUI);
  syncUI();

  askBtn.addEventListener("click", async (e) => {
    e.preventDefault();

    const question = (questionInput.value || "").trim();
    const tipPicked = tipSelect && tipSelect.selectedIndex > 0;
    const modelPicked = modelSelect && modelSelect.selectedIndex > 0;

    if (!tipPicked || !modelPicked) {
      alert("Selectează tipul și metoda!");
      return;
    }
    if (!question) {
      alert("Scrie o întrebare înainte de a trimite!");
      return;
    }

    const tip = tipSelect.value;      // trimitem “MinMax/Asignari/Nash/etc”
    const model = modelSelect.value;  // trimitem “AlphaBeta/Template/Optim-Mode”

    answerBox.innerHTML = `<p style="color:#aaa;font-style:italic;">Se procesează...</p>`;

    try {
      const res = await fetch(`${API_BASE}/smartest/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, model, tip })
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        answerBox.innerHTML = `<p style="color:red;">${data.error || "Eroare la server."}</p>`;
        return;
      }

      answerBox.innerHTML = `<p>${(data.answer || "").replaceAll("\n", "<br>")}</p>`;
    } catch (err) {
      console.error(err);
      answerBox.innerHTML = `<p style="color:red;">Eroare la obținerea răspunsului.</p>`;
    }
  });
});
