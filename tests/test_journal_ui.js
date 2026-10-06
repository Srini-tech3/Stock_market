/* Offline DOM contract checks for status-driven KPI updates. No dependencies. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function journalUI(fetch) {
    let onChange;
    const label = { textContent: "Open" };
    const icon = { setAttribute() {} };
    const badge = { querySelector: (selector) => selector === ".status-label" ? label : icon };
    const row = { dataset: { entryId: "fixture", tradeStatus: "open" }, querySelector: () => badge };
    const control = { checked: true, disabled: false, closest: () => row, matches: () => true };
    const table = {
        dataset: { statusUrl: "/api/journal/status" },
        querySelectorAll: () => [control],
        addEventListener: (event, handler) => { onChange = handler; }
    };
    const cards = Object.entries({ capital: "₹300,000.00", total_profit: "₹1,000.00", total_loss: "₹200.00",
        used_capital: "₹50,000.00", available_capital: "₹251,000.00" })
        .map(([key, textContent]) => ({ dataset: { journalKpi: key }, textContent }));
    const message = { textContent: "" };
    const counts = { open: { textContent: "1 Open" }, closed: { textContent: "0 Closed" } };
    const document = {
        getElementById: (id) => id === "journalTable" ? table : message,
        querySelectorAll: () => cards,
        querySelector: (selector) => counts[selector.includes("openTradeCount") ? "open" : "closed"]
    };
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../Script/static/js/journal.js"), "utf8"),
        { document, fetch, Intl });
    return { control, row, cards, message, counts, change: () => onChange({ target: control }) };
}

const closedResult = {
    success: true, status: "closed", counts: { open: 0, closed: 1 },
    kpis: { capital: 300000, total_profit: 1000, total_loss: 200, used_capital: 0, available_capital: 301000 }
};

test("successful status save updates KPI cards and counts without reloading", async () => {
    const ui = journalUI(async (url, options) => {
        assert.equal(url, "/api/journal/status");
        assert.deepEqual(JSON.parse(options.body), { entry_id: "fixture", status: "closed" });
        return { ok: true, json: async () => closedResult };
    });
    ui.control.checked = false;
    await ui.change();
    assert.equal(ui.row.dataset.tradeStatus, "closed");
    assert.equal(ui.cards[3].textContent, "₹0.00");
    assert.equal(ui.cards[4].textContent, "₹301,000.00");
    assert.equal(ui.counts.open.textContent, "0 Open");
    assert.equal(ui.control.disabled, false);
});

test("failed save restores control and leaves KPI amounts untouched", async () => {
    const ui = journalUI(async () => ({ ok: false, json: async () => ({ success: false, error: "Save failed" }) }));
    const before = ui.cards.map((card) => card.textContent);
    ui.control.checked = false;
    await ui.change();
    assert.equal(ui.control.checked, true);
    assert.equal(ui.row.dataset.tradeStatus, "open");
    assert.deepEqual(ui.cards.map((card) => card.textContent), before);
    assert.match(ui.message.textContent, /Save failed/);
    assert.equal(ui.control.disabled, false);
});

test("unavailable amounts are rendered as a dash after a successful save", async () => {
    const ui = journalUI(async () => ({ ok: true, json: async () => ({
        ...closedResult, kpis: { ...closedResult.kpis, total_profit: null, available_capital: null }
    }) }));
    ui.control.checked = false;
    await ui.change();
    assert.equal(ui.cards[1].textContent, "—");
    assert.equal(ui.cards[4].textContent, "—");
});
