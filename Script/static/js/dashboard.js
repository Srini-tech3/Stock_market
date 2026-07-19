document.addEventListener("DOMContentLoaded",function(){
flatpickr("#expiryDate",{
dateFormat:"Y-m-d",
allowInput:false,
clickOpens:true
});
});

const strategyFilter = document.getElementById("strategyFilter");
const rankFilter = document.getElementById("rankFilter");

function applyFilters() {

    const selectedStrategy = strategyFilter.value;
    const selectedRank = rankFilter.value;

    const rows = document.querySelectorAll(".strategy-table tbody tr");

    let visibleCount = 0;

    rows.forEach(row => {

        const strategy = row.dataset.strategy;
        const rank = parseInt(row.dataset.rank);

        // Strategy condition
        const strategyMatch =
            selectedStrategy === "all" ||
            strategy === selectedStrategy;

        // Rank condition
        const rankMatch =
            selectedRank === "all" ||
            rank <= parseInt(selectedRank);

        if (strategyMatch && rankMatch) {
            row.style.display = "";
            visibleCount++;
        } else {
            row.style.display = "none";
        }

    });
    document.getElementById("strategyCount").textContent = visibleCount;
}

strategyFilter.addEventListener("change", applyFilters);

rankFilter.addEventListener("change", applyFilters);

document.getElementById("clearFilters").addEventListener("click", () => {

    strategyFilter.value = "all";
    rankFilter.value = "all";

    // Reset sorting
    resetSort();

    // Apply filters (All + All)
    applyFilters();

});

const table = document.getElementById("strategyTable");
const tbody = document.getElementById("strategyTableBody");

const originalRows = Array.from(tbody.querySelectorAll("tr"));

let currentSortColumn = -1;
let currentSortDirection = "asc";

document.querySelectorAll(".sortable").forEach(header => {

    header.addEventListener("click", function () {

        const column = Number(this.dataset.column);
        const type = this.dataset.type;

        sortTable(column, type);

    });

});

function sortTable(column, type) {

    const rows = Array.from(tbody.querySelectorAll("tr"));

    // Toggle sort direction
    if (currentSortColumn === column) {
        currentSortDirection =
            currentSortDirection === "asc" ? "desc" : "asc";
    } else {
        currentSortColumn = column;
        currentSortDirection = "asc";
    }

    rows.sort((a, b) => {

        let valueA = a.cells[column].innerText.trim();
        let valueB = b.cells[column].innerText.trim();

        // Number / Currency
        if (type === "number" || type === "currency") {

            valueA = parseFloat(valueA.replace(/[₹,%⭐,\s]/g, "")) || 0;
            valueB = parseFloat(valueB.replace(/[₹,%⭐,\s]/g, "")) || 0;

        }

        // Date
        else if (type === "date") {

            valueA = new Date(valueA);
            valueB = new Date(valueB);

        }

        // Text
        else {

            valueA = valueA.toLowerCase();
            valueB = valueB.toLowerCase();

        }

        if (valueA < valueB)
            return currentSortDirection === "asc" ? -1 : 1;

        if (valueA > valueB)
            return currentSortDirection === "asc" ? 1 : -1;

        return 0;

    });

    rows.forEach(row => tbody.appendChild(row));
    // Reset all sort icons
    document.querySelectorAll(".sort-icon").forEach(icon => {
        icon.className = "sort-icon";
        icon.style.visibility = "hidden";
    });

    // Show icon for active column
    const activeHeader = document.querySelector(
        `.sortable[data-column="${column}"] .sort-icon`
    );

    activeHeader.style.visibility = "visible";

    if (currentSortDirection === "asc") {
        activeHeader.classList.add("bi", "bi-arrow-up");
    } else {
        activeHeader.classList.add("bi", "bi-arrow-down");
    }
}

function resetSort() {

    // Restore original row order
    originalRows.forEach(row => tbody.appendChild(row));

    // Reset sort state
    currentSortColumn = -1;
    currentSortDirection = "asc";

    // Hide all sort icons
    document.querySelectorAll(".sort-icon").forEach(icon => {
        icon.className = "sort-icon";
        icon.style.visibility = "hidden";
    });

}

async function runAnalysis() {

    const button = document.getElementById("runAnalysisBtn");
    const expiry = document.getElementById("expiryDate").value;

    if (!expiry) {
        alert("Please select an expiry date.");
        return;
    }

    // Save original button HTML
    const originalHTML = button.innerHTML;

    // Disable button
    button.disabled = true;

    // Show loading state
    button.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2"></span>
        Running...
    `;

    try {

        const response = await fetch("/run-analysis", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                expiry: expiry
            })
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || "Analysis failed.");
        }

        // Refresh dashboard
        location.reload();

    } catch (error) {

        alert(error.message);

    } finally {

        button.disabled = false;
        button.innerHTML = originalHTML;

    }

}

document.getElementById("runAnalysisBtn").addEventListener("click", runAnalysis);