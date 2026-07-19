document.addEventListener("DOMContentLoaded", () => {

    const expiry = document.getElementById("expiry");

    expiry.innerHTML = `

        <option>31-Jul-2026</option>

        <option>07-Aug-2026</option>

        <option>14-Aug-2026</option>

    `;

    document
    .getElementById("lastUpdate")
    .innerHTML = new Date().toLocaleString();

});

document
.getElementById("runBtn")
.addEventListener("click", ()=>{

    const expiry =
    document.getElementById("expiry").value;

    alert("Running Strategy for : " + expiry);

});