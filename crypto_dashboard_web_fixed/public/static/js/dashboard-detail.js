const coinDetails = window.cryptoCoinDetails || {};
const detailPanel = document.getElementById("coinDetailPanel");
const coinButtons = document.querySelectorAll("[data-coin-select]");
const coinRows = document.querySelectorAll("[data-coin-row]");
const summaryButton = document.getElementById("generatePerformanceSummary");
const summaryPanel = document.getElementById("performanceSummaryPanel");

function money(value) {
    const number = Number(value || 0);
    return `USD ${number.toLocaleString("es-AR", { maximumFractionDigits: 2 })}`;
}

function amount(value) {
    const number = Number(value || 0);
    return number.toLocaleString("es-AR", { maximumFractionDigits: 8 });
}

function read(record, keys, fallback = 0) {
    if (!record) return fallback;

    for (const key of keys) {
        if (Object.prototype.hasOwnProperty.call(record, key)) {
            return record[key];
        }
    }

    const normalizedKeys = Object.keys(record).map((key) => ({
        raw: key,
        normalized: key.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""),
    }));

    for (const key of keys) {
        const normalizedWanted = key.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const match = normalizedKeys.find((item) => item.normalized === normalizedWanted);
        if (match) {
            return record[match.raw];
        }
    }

    if (keys.some((key) => key.toLowerCase().includes("dolares"))) {
        const wanted = keys.join(" ").toLowerCase();
        const token = wanted.includes("comprados")
            ? "comprados"
            : wanted.includes("vendidos")
              ? "vendidos"
              : wanted.includes("abiertos")
                ? "abiertos"
                : "";
        const match = normalizedKeys.find((item) => item.normalized.includes("lares") && item.normalized.includes(token));
        if (match) {
            return record[match.raw];
        }
    }

    return fallback;
}

function statusBadge(value) {
    const status = String(value || "").toUpperCase();
    const className = status === "CERRADA" ? "badge text-bg-secondary" : "badge text-bg-success";
    return `<span class="${className}">${status || "SIN ESTADO"}</span>`;
}

function metric(label, value, tone = "") {
    return `
        <div class="detail-metric ${tone}">
            <span>${label}</span>
            <strong>${value}</strong>
        </div>
    `;
}

function tradeHighlight(title, trade, emptyText) {
    if (!trade) {
        return `
            <div class="trade-highlight muted">
                <span>${title}</span>
                <strong>${emptyText}</strong>
            </div>
        `;
    }

    const pnl = Number(read(trade, ["PNL realizado"], 0));
    const tone = pnl >= 0 ? "positive" : "negative";

    return `
        <div class="trade-highlight ${tone}">
            <span>${title}</span>
            <strong>${money(pnl)}</strong>
            <small>${read(trade, ["Fecha venta"], "-")} - ${amount(read(trade, ["Cantidad vendida"], 0))} unidades - Venta ${money(read(trade, ["Dolares vendidos"], 0))}</small>
        </div>
    `;
}

function allSales() {
    return Object.entries(coinDetails).flatMap(([coin, detail]) =>
        (detail.ventas || []).map((trade) => ({ ...trade, Moneda: coin })),
    );
}

function sortedCoinsBy(field, direction = "desc") {
    const multiplier = direction === "asc" ? 1 : -1;

    return Object.entries(coinDetails)
        .map(([coin, detail]) => ({
            coin,
            resumen: detail.resumen || {},
            metricas: detail.metricas || {},
            value: Number(read(detail.resumen || {}, [field], 0)),
        }))
        .sort((a, b) => (a.value - b.value) * multiplier);
}

function summaryCard(label, value, note, tone = "") {
    return `
        <div class="summary-card ${tone}">
            <span>${label}</span>
            <strong>${value}</strong>
            <small>${note}</small>
        </div>
    `;
}

function formatTradeLine(trade) {
    if (!trade) return "Sin ventas registradas";

    const pnl = Number(read(trade, ["PNL realizado"], 0));
    return `${trade.Moneda || read(trade, ["Nombre"], "-")} - ${read(trade, ["Fecha venta"], "-")} - ${money(pnl)}`;
}

function renderPerformanceSummary() {
    if (!summaryPanel) return;

    const sales = allSales();
    const positiveSales = sales.filter((trade) => Number(read(trade, ["PNL realizado"], 0)) > 0);
    const negativeSales = sales.filter((trade) => Number(read(trade, ["PNL realizado"], 0)) < 0);
    const bestTrade = sales.slice().sort((a, b) => Number(read(b, ["PNL realizado"], 0)) - Number(read(a, ["PNL realizado"], 0)))[0];
    const worstTrade = sales.slice().sort((a, b) => Number(read(a, ["PNL realizado"], 0)) - Number(read(b, ["PNL realizado"], 0)))[0];
    const worstLoss = negativeSales.slice().sort((a, b) => Number(read(a, ["PNL realizado"], 0)) - Number(read(b, ["PNL realizado"], 0)))[0];
    const bestCoinByPnl = sortedCoinsBy("PNL cerrado total")[0];
    const worstCoinByPnl = sortedCoinsBy("PNL cerrado total", "asc")[0];
    const bestCoinByRoi = sortedCoinsBy("ROI %")[0];
    const totalPnl = sales.reduce((sum, trade) => sum + Number(read(trade, ["PNL realizado"], 0)), 0);
    const winRate = sales.length ? (positiveSales.length / sales.length) * 100 : 0;

    summaryPanel.hidden = false;
    summaryPanel.innerHTML = `
        <div class="summary-grid">
            ${summaryCard(
                "Mejor trade",
                bestTrade ? money(read(bestTrade, ["PNL realizado"], 0)) : "Sin ventas",
                bestTrade ? `${bestTrade.Moneda} - ${read(bestTrade, ["Fecha venta"], "-")} - Venta ${money(read(bestTrade, ["Dolares vendidos"], 0))}` : "Todavia no hay operaciones vendidas.",
                "positive",
            )}
            ${summaryCard(
                "Peor perdida realizada",
                worstLoss ? money(read(worstLoss, ["PNL realizado"], 0)) : "Sin perdidas",
                worstLoss ? `${worstLoss.Moneda} - ${read(worstLoss, ["Fecha venta"], "-")} - Costo ${money(read(worstLoss, ["Costo proporcional"], 0))}` : "No hay ventas con PNL negativo.",
                worstLoss ? "negative" : "positive",
            )}
            ${summaryCard(
                "Mejor moneda por PNL",
                bestCoinByPnl ? bestCoinByPnl.coin : "-",
                bestCoinByPnl ? `${money(bestCoinByPnl.value)} realizados - ROI ${read(bestCoinByPnl.resumen, ["ROI %"], 0)}%` : "Sin monedas procesadas.",
                bestCoinByPnl && bestCoinByPnl.value >= 0 ? "positive" : "negative",
            )}
            ${summaryCard(
                "Moneda mas floja",
                worstCoinByPnl ? worstCoinByPnl.coin : "-",
                worstCoinByPnl ? `${money(worstCoinByPnl.value)} realizados - ROI ${read(worstCoinByPnl.resumen, ["ROI %"], 0)}%` : "Sin monedas procesadas.",
                worstCoinByPnl && worstCoinByPnl.value < 0 ? "negative" : "",
            )}
        </div>

        <div class="summary-insights">
            <div>
                <h3>Lectura del archivo</h3>
                <ul>
                    <li>PNL realizado total: <strong class="${totalPnl >= 0 ? "text-success" : "text-danger"}">${money(totalPnl)}</strong>.</li>
                    <li>Ventas con ganancia: <strong>${positiveSales.length}</strong> de <strong>${sales.length}</strong> (${winRate.toFixed(2)}% win rate).</li>
                    <li>Mejor ROI por moneda: <strong>${bestCoinByRoi ? bestCoinByRoi.coin : "-"}</strong>${bestCoinByRoi ? ` con ${read(bestCoinByRoi.resumen, ["ROI %"], 0)}%.` : "."}</li>
                    <li>Mejor trade detectado: <strong>${formatTradeLine(bestTrade)}</strong>.</li>
                    <li>Peor trade detectado: <strong>${formatTradeLine(worstTrade)}</strong>.</li>
                </ul>
            </div>
            <div class="summary-actions-list">
                <h3>Accesos rapidos</h3>
                <div>
                    ${bestCoinByPnl ? `<button class="summary-link" type="button" data-coin-select="${bestCoinByPnl.coin}">Abrir mejor moneda (${bestCoinByPnl.coin})</button>` : ""}
                    ${worstCoinByPnl ? `<button class="summary-link" type="button" data-coin-select="${worstCoinByPnl.coin}">Revisar peor moneda (${worstCoinByPnl.coin})</button>` : ""}
                    ${worstLoss ? `<button class="summary-link" type="button" data-coin-select="${worstLoss.Moneda}">Ver perdida de ${worstLoss.Moneda}</button>` : ""}
                </div>
            </div>
        </div>
    `;

    summaryPanel.querySelectorAll("[data-coin-select]").forEach((button) => {
        button.addEventListener("click", () => renderCoin(button.dataset.coinSelect));
    });
}

function renderTable(title, rows, columns, emptyText) {
    if (!rows.length) {
        return `
            <div class="detail-table-block">
                <h3>${title}</h3>
                <div class="detail-empty slim">${emptyText}</div>
            </div>
        `;
    }

    const header = columns.map((column) => `<th>${column.label}</th>`).join("");
    const body = rows
        .map((row) => {
            const cells = columns.map((column) => `<td>${column.render(row)}</td>`).join("");
            return `<tr>${cells}</tr>`;
        })
        .join("");

    return `
        <div class="detail-table-block">
            <h3>${title}</h3>
            <div class="table-responsive">
                <table class="table table-dark table-hover align-middle detail-table">
                    <thead><tr>${header}</tr></thead>
                    <tbody>${body}</tbody>
                </table>
            </div>
        </div>
    `;
}

function setActiveCoin(coin) {
    coinButtons.forEach((button) => button.classList.toggle("is-active", button.dataset.coinSelect === coin));
    coinRows.forEach((row) => row.classList.toggle("is-active", row.dataset.coinRow === coin));
}

function renderCoin(coin) {
    const detail = coinDetails[coin];
    if (!detail || !detailPanel) return;

    const resumen = detail.resumen || {};
    const metricas = detail.metricas || {};
    const pnl = Number(read(resumen, ["PNL cerrado total"], 0));
    const pnlTone = pnl >= 0 ? "positive" : "negative";

    detailPanel.innerHTML = `
        <div class="detail-title-row">
            <div>
                <span class="detail-label">Moneda seleccionada</span>
                <h2>${coin}</h2>
            </div>
            <span class="detail-result ${pnlTone}">${money(pnl)}</span>
        </div>

        <div class="detail-metrics-grid">
            ${metric("Invertido", money(read(resumen, ["Dolares invertidos"], 0)))}
            ${metric("Vendido", money(read(resumen, ["Dolares vendidos"], 0)))}
            ${metric("Capital abierto", money(read(resumen, ["Dolares abiertos"], 0)))}
            ${metric("ROI", `${read(resumen, ["ROI %"], 0)}%`, pnlTone)}
            ${metric("Abiertas", read(resumen, ["Operaciones abiertas"], 0))}
            ${metric("Cerradas", read(resumen, ["Operaciones cerradas"], 0))}
            ${metric("Win rate", `${read(metricas, ["win_rate"], 0)}%`)}
            ${metric("Precio promedio", money(read(metricas, ["precio_promedio_compra"], 0)))}
        </div>

        <div class="trade-highlight-grid">
            ${tradeHighlight("Mejor trade", detail.mejor_trade, "Sin ventas registradas")}
            ${tradeHighlight("Peor trade", detail.peor_trade, "Sin ventas registradas")}
            <div class="trade-highlight">
                <span>Cantidad restante</span>
                <strong>${amount(read(metricas, ["cantidad_restante"], 0))}</strong>
                <small>${read(metricas, ["operaciones_totales"], 0)} movimientos totales - ${read(metricas, ["ventas_realizadas"], 0)} ventas realizadas</small>
            </div>
        </div>

        <div class="detail-tabs">
            ${renderTable(
                "Operaciones abiertas",
                detail.abiertas || [],
                [
                    { label: "ID", render: (row) => read(row, ["ID"], "-") },
                    { label: "Fecha", render: (row) => read(row, ["Fecha de compra"], "-") },
                    { label: "Comprado", render: (row) => amount(read(row, ["Cantidad comprada"], 0)) },
                    { label: "Restante", render: (row) => amount(read(row, ["Cantidad restante"], 0)) },
                    { label: "Invertido", render: (row) => money(read(row, ["Dolares comprados"], 0)) },
                    { label: "Estado", render: (row) => statusBadge(read(row, ["Estado"], "")) },
                ],
                "No hay operaciones abiertas para esta moneda.",
            )}
            ${renderTable(
                "Operaciones cerradas",
                detail.cerradas || [],
                [
                    { label: "ID", render: (row) => read(row, ["ID"], "-") },
                    { label: "Fecha", render: (row) => read(row, ["Fecha de compra"], "-") },
                    { label: "Comprado", render: (row) => amount(read(row, ["Cantidad comprada"], 0)) },
                    { label: "Vendido", render: (row) => amount(read(row, ["Cantidad vendida total"], 0)) },
                    { label: "Invertido", render: (row) => money(read(row, ["Dolares comprados"], 0)) },
                    { label: "Estado", render: (row) => statusBadge(read(row, ["Estado"], "")) },
                ],
                "No hay operaciones cerradas para esta moneda.",
            )}
            ${renderTable(
                "Ventas y PNL realizado",
                detail.ventas || [],
                [
                    { label: "Fecha", render: (row) => read(row, ["Fecha venta"], "-") },
                    { label: "Cantidad", render: (row) => amount(read(row, ["Cantidad vendida"], 0)) },
                    { label: "Precio", render: (row) => money(read(row, ["Precio venta"], 0)) },
                    { label: "Vendido", render: (row) => money(read(row, ["Dolares vendidos"], 0)) },
                    { label: "Costo", render: (row) => money(read(row, ["Costo proporcional"], 0)) },
                    { label: "PNL", render: (row) => {
                        const value = Number(read(row, ["PNL realizado"], 0));
                        const className = value >= 0 ? "text-success" : "text-danger";
                        return `<strong class="${className}">${money(value)}</strong>`;
                    } },
                ],
                "No hay ventas registradas para esta moneda.",
            )}
        </div>
    `;

    setActiveCoin(coin);
    detailPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function coinFromPlotlyPoint(point) {
    if (!point) return "";
    return String(point.x || point.label || point.customdata || "").trim();
}

coinButtons.forEach((button) => {
    button.addEventListener("click", () => renderCoin(button.dataset.coinSelect));
});

coinRows.forEach((row) => {
    row.addEventListener("click", () => renderCoin(row.dataset.coinRow));
});

if (summaryButton) {
    summaryButton.addEventListener("click", renderPerformanceSummary);
}

window.addEventListener("load", () => {
    document.querySelectorAll(".js-plotly-plot").forEach((plot) => {
        if (!plot.on) return;

        plot.on("plotly_click", (event) => {
            const coin = coinFromPlotlyPoint(event.points && event.points[0]);
            if (coinDetails[coin]) {
                renderCoin(coin);
            }
        });
    });

    const firstCoin = Object.keys(coinDetails)[0];
    if (firstCoin) {
        renderCoin(firstCoin);
    }
});
