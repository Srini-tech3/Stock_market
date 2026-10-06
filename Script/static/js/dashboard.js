"use strict";

// Dashboard-only script; all bindings are guarded and no external CDN is needed.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("scanForm");
    const strategy = document.getElementById("strategyFilter");
    const rank = document.getElementById("rankFilter");
    const message = document.getElementById("scanMessage");
    const tbody = document.getElementById("strategyTableBody");
    const originalRows = tbody ? Array.from(tbody.querySelectorAll("tr[data-strategy]")) : [];
    let sortColumn = null;
    let ascending = true;

    document.querySelectorAll(".sort-button").forEach(button => {
        button.addEventListener("click", () => {
            if (!tbody) return;
            const column = Number(button.dataset.column);
            ascending = sortColumn === column ? !ascending : true;
            sortColumn = column;
            const numeric = button.dataset.type === "number";
            const value = row => {
                const text = row.cells[column].textContent.trim();
                return numeric ? Number(text.replace(/[^0-9.\-]/g, "")) : text.toLowerCase();
            };
            const rows = Array.from(tbody.querySelectorAll("tr[data-strategy]"));
            rows.sort((a, b) => (value(a) < value(b) ? -1 : value(a) > value(b) ? 1 : 0) * (ascending ? 1 : -1));
            rows.forEach(row => tbody.appendChild(row));
            document.querySelectorAll("#strategyTable th").forEach(th => th.removeAttribute("aria-sort"));
            button.closest("th").setAttribute("aria-sort", ascending ? "ascending" : "descending");
        });
    });

    function applyFilters() {
        if (!strategy || !rank) return;
        let count = 0;
        document.querySelectorAll("#strategyTableBody tr[data-strategy]").forEach(row => {
            const matches = (strategy.value === "all" || row.dataset.strategy === strategy.value)
                && (rank.value === "all" || Number(row.dataset.rank) <= Number(rank.value));
            row.hidden = !matches;
            if (matches) count++;
        });
        const counter = document.getElementById("strategyCount");
        if (counter) counter.textContent = String(count);
    }

    strategy?.addEventListener("change", applyFilters);
    rank?.addEventListener("change", applyFilters);
    document.getElementById("clearFilters")?.addEventListener("click", () => {
        strategy.value = "all";
        rank.value = "2";
        originalRows.forEach(row => tbody.appendChild(row));
        sortColumn = null;
        ascending = true;
        document.querySelectorAll("#strategyTable th").forEach(th => th.removeAttribute("aria-sort"));
        applyFilters();
    });
    applyFilters();

    document.getElementById("refreshBtn")?.addEventListener("click", () => window.location.reload());
    document.getElementById("showGreeks")?.addEventListener("change", event => {
        document.getElementById("chainTable")?.classList.toggle("show-greeks", event.target.checked);
    });

    form?.addEventListener("submit", async event => {
        event.preventDefault();
        const expiry = document.getElementById("expiryDate").value;
        const marketSource = document.getElementById("marketSource").value;
        const button = document.getElementById("runAnalysisBtn");
        if (!expiry || button.disabled) return;
        button.disabled = true;
        button.textContent = "Scanning…";
        message.className = "scan-message";
        message.textContent = "Processing your CSV and updating the Excel journal. No orders will be placed.";
        try {
            const response = await fetch("/run-analysis", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ expiry, market_source: marketSource })
            });
            const result = await response.json();
            if (!response.ok || !result.success) throw new Error(result.error || "Scan failed.");
            // Show the append result once after reloading the saved snapshot.
            sessionStorage.setItem("lastScanMessage", `Scan complete: ${result.bull_put} Bull Put / ${result.bear_call} Bear Call setups. ${result.journal_rows_added} journal rows appended. Identical repeat entries are skipped.`);
            window.location.reload();
        } catch (error) {
            message.className = "scan-message error";
            message.textContent = error.message || "Unable to contact the app. Check that it is running.";
        } finally {
            button.disabled = false;
            button.textContent = "Run practice scan";
        }
    });

    const savedMessage = sessionStorage.getItem("lastScanMessage");
    if (savedMessage && message) {
        message.className = "scan-message success";
        message.textContent = savedMessage;
        sessionStorage.removeItem("lastScanMessage");
    }
});
