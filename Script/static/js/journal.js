/* Manual dashboard status selections only. Never writes Excel or runs a scan. */
(() => {
    "use strict";
    const table = document.getElementById("journalTable");
    if (!table) return;
    const message = document.getElementById("journalStatusMessage");
    const toggles = Array.from(table.querySelectorAll(".journal-status-toggle"));
    const amountFormat = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    let saving = false;

    table.addEventListener("change", async (event) => {
        const control = event.target;
        if (!control.matches(".journal-status-toggle")) return;
        const row = control.closest("tr");
        const previous = row.dataset.tradeStatus === "open";
        if (saving) {
            control.checked = previous;
            return;
        }
        const status = control.checked ? "open" : "closed";
        saving = true;
        toggles.forEach((toggle) => { toggle.disabled = true; });
        message.className = "scan-message";
        message.textContent = "Saving trade selection…";
        try {
            const response = await fetch(table.dataset.statusUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ entry_id: row.dataset.entryId, status })
            });
            const result = await response.json();
            if (!response.ok || !result.success) throw new Error(result.error || "Unable to save trade selection.");
            row.dataset.tradeStatus = result.status;
            control.checked = result.status === "open";
            const badge = row.querySelector(".trade-status");
            const label = result.status === "open" ? "Open" : "Closed";
            badge.className = `trade-status trade-status-${result.status}`;
            badge.title = `Trade control is ${control.checked ? "on" : "off"}: ${label}`;
            badge.querySelector(".status-label").textContent = label;
            badge.querySelector(".status-icon-path").setAttribute("d", control.checked ? "M12 7v5l3 2" : "m8 12 3 3 5-6");
            for (const state of ["open", "closed"]) {
                document.querySelector(`#${state}TradeCount .status-label`).textContent = `${result.counts[state]} ${state === "open" ? "Open" : "Closed"}`;
            }
            document.querySelectorAll("[data-journal-kpi]").forEach((card) => {
                const amount = result.kpis[card.dataset.journalKpi];
                card.textContent = typeof amount === "number" && Number.isFinite(amount) ? `₹${amountFormat.format(amount)}` : "—";
            });
            message.className = "scan-message success";
            message.textContent = `Trade marked ${label}. Selection saved; Excel is unchanged.`;
        } catch (error) {
            control.checked = previous;
            message.className = "scan-message error";
            message.textContent = `${error.message || "Unable to save trade selection."} Refresh Journal to check the saved state.`;
        } finally {
            saving = false;
            toggles.forEach((toggle) => { toggle.disabled = toggle.closest("tr").dataset.tradeStatus === "unknown"; });
        }
    });
})();
