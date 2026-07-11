import os
import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
# Vercel Functions solo permite escrituras temporales en /tmp. En desarrollo
# conservamos la carpeta uploads para que el comportamiento local no cambie.
UPLOAD_FOLDER = Path(tempfile.gettempdir()) if os.environ.get("VERCEL") else BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}
QUOTE_ASSETS = [
    "USDT",
    "USDC",
    "BUSD",
    "FDUSD",
    "TUSD",
    "DAI",
    "USD",
    "EUR",
    "BTC",
    "ETH",
    "BNB",
    "BRL",
    "ARS",
]

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "clave-local-solo-desarrollo")

COLUMNAS_COMPRAS = [
    "ID",
    "Nombre",
    "Fecha de compra",
    "Dólares comprados",
    "Precio de compra",
    "Cantidad comprada",
    "Cantidad vendida total",
    "Cantidad restante",
    "Estado",
]

COLUMNAS_VENTAS = [
    "ID venta",
    "ID compra",
    "Nombre",
    "Fecha venta",
    "Cantidad vendida",
    "Precio venta",
    "Dólares vendidos",
    "Costo proporcional",
    "PNL realizado",
]


def extension_permitida(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def normalizar_nombre_columna(nombre: str) -> str:
    return "".join(caracter for caracter in str(nombre).lower() if caracter.isalnum())


def buscar_columna(df: pd.DataFrame, posibles_nombres: list[str]) -> str | None:
    columnas_normalizadas = {normalizar_nombre_columna(columna): columna for columna in df.columns}

    for nombre in posibles_nombres:
        columna = columnas_normalizadas.get(normalizar_nombre_columna(nombre))
        if columna:
            return columna

    return None


def numero_desde_texto(valor) -> float:
    if pd.isna(valor):
        return 0.0

    texto = str(valor).strip().replace(",", "")
    partes = texto.split()
    candidato = partes[0] if partes else texto
    numero = pd.to_numeric(candidato, errors="coerce")
    return 0.0 if pd.isna(numero) else float(numero)


def extraer_moneda_base(par: str) -> str:
    par = str(par).upper().replace("/", "").replace("-", "").replace("_", "").strip()

    for quote in sorted(QUOTE_ASSETS, key=len, reverse=True):
        if par.endswith(quote) and len(par) > len(quote):
            return par[: -len(quote)]

    return par


def parece_export_binance(df: pd.DataFrame) -> bool:
    columnas_requeridas = [
        buscar_columna(df, ["Date(UTC)", "Date", "Time", "UTC_Time", "Order Time", "Fecha", "Hora"]),
        buscar_columna(df, ["Pair", "Market", "Symbol", "Trading Pair", "Par"]),
        buscar_columna(df, ["Side", "Type", "Buy/Sell", "Lado"]),
    ]
    return all(columnas_requeridas)


def convertir_binance_a_formato_interno(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    columna_fecha = buscar_columna(df, ["Date(UTC)", "Date", "Time", "UTC_Time", "Order Time", "Fecha", "Hora"])
    columna_par = buscar_columna(df, ["Pair", "Market", "Symbol", "Trading Pair", "Par"])
    columna_lado = buscar_columna(df, ["Side", "Type", "Buy/Sell", "Lado"])
    columna_precio = buscar_columna(df, ["Price", "Average Price", "Avg Price", "Filled Price", "Precio", "Precio promedio"])
    columna_cantidad = buscar_columna(df, ["Executed", "Amount Executed", "Quantity", "Qty", "Filled", "Cantidad", "Ejecutado"])
    columna_total = buscar_columna(df, ["Amount", "Total", "Quote Amount", "Filled Total", "Subtotal", "Total_Cotizacion", "Total de trading"])

    if not all([columna_fecha, columna_par, columna_lado, columna_precio, columna_cantidad]):
        raise ValueError("El archivo parece ser de Binance, pero faltan columnas para convertirlo.")

    compras = []
    ventas = []
    lotes_abiertos: dict[str, list[dict]] = {}
    id_compra = 1
    id_venta = 1

    operaciones = df.copy()
    operaciones["_fecha"] = pd.to_datetime(operaciones[columna_fecha], errors="coerce")
    operaciones = operaciones.sort_values("_fecha", na_position="last")

    for _, fila in operaciones.iterrows():
        lado = str(fila[columna_lado]).upper().strip()
        if lado not in {"BUY", "SELL"}:
            continue

        moneda = extraer_moneda_base(fila[columna_par])
        fecha = fila["_fecha"].strftime("%d-%m-%Y") if pd.notna(fila["_fecha"]) else str(fila[columna_fecha])
        precio = numero_desde_texto(fila[columna_precio])
        cantidad = numero_desde_texto(fila[columna_cantidad])
        total = numero_desde_texto(fila[columna_total]) if columna_total else precio * cantidad

        if cantidad <= 0:
            continue

        if lado == "BUY":
            compra = {
                "ID": id_compra,
                "Nombre": moneda,
                "Fecha de compra": fecha,
                "Dólares comprados": round(total, 2),
                "Precio de compra": round(precio, 8),
                "Cantidad comprada": cantidad,
                "Cantidad vendida total": 0.0,
                "Cantidad restante": cantidad,
                "Estado": "ABIERTA",
            }
            compras.append(compra)
            lotes_abiertos.setdefault(moneda, []).append(compra)
            id_compra += 1
            continue

        cantidad_por_vender = cantidad
        costo_total = 0.0
        ids_compra = []

        for compra in lotes_abiertos.get(moneda, []):
            if cantidad_por_vender <= 0:
                break

            disponible = float(compra["Cantidad restante"])
            if disponible <= 0:
                continue

            consumido = min(disponible, cantidad_por_vender)
            costo_unitario = float(compra["Dólares comprados"]) / float(compra["Cantidad comprada"])
            costo_total += consumido * costo_unitario

            compra["Cantidad vendida total"] += consumido
            compra["Cantidad restante"] -= consumido
            compra["Estado"] = "CERRADA" if compra["Cantidad restante"] <= 0.00000001 else "ABIERTA"
            ids_compra.append(str(compra["ID"]))
            cantidad_por_vender -= consumido

        ventas.append(
            {
                "ID venta": id_venta,
                "ID compra": int(ids_compra[0]) if ids_compra else 0,
                "Nombre": moneda,
                "Fecha venta": fecha,
                "Cantidad vendida": cantidad,
                "Precio venta": round(precio, 8),
                "Dólares vendidos": round(total, 2),
                "Costo proporcional": round(costo_total, 2),
                "PNL realizado": round(total - costo_total, 2) if costo_total else 0.0,
            }
        )
        id_venta += 1

    if not compras and not ventas:
        raise ValueError("No se encontraron compras o ventas reconocibles en el archivo de Binance.")

    return pd.DataFrame(compras, columns=COLUMNAS_COMPRAS), pd.DataFrame(ventas, columns=COLUMNAS_VENTAS)


def convertir_columnas_compras(compras: pd.DataFrame) -> pd.DataFrame:
    compras = compras.copy()
    columnas_float = [
        "Dólares comprados",
        "Precio de compra",
        "Cantidad comprada",
        "Cantidad vendida total",
        "Cantidad restante",
    ]

    for columna in columnas_float:
        if columna in compras.columns:
            compras[columna] = pd.to_numeric(compras[columna], errors="coerce").fillna(0.0)

    if "ID" in compras.columns:
        compras["ID"] = pd.to_numeric(compras["ID"], errors="coerce").fillna(0).astype(int)

    if "Estado" in compras.columns:
        compras["Estado"] = compras["Estado"].fillna("ABIERTA").astype(str).str.upper()

    return compras


def convertir_columnas_ventas(ventas: pd.DataFrame) -> pd.DataFrame:
    ventas = ventas.copy()
    columnas_numericas = [
        "ID venta",
        "ID compra",
        "Cantidad vendida",
        "Precio venta",
        "Dólares vendidos",
        "Costo proporcional",
        "PNL realizado",
    ]

    for columna in columnas_numericas:
        if columna in ventas.columns:
            ventas[columna] = pd.to_numeric(ventas[columna], errors="coerce").fillna(0.0)

    if "Nombre" in ventas.columns:
        ventas["Nombre"] = ventas["Nombre"].fillna("Sin nombre")

    return ventas


def validar_columnas(df: pd.DataFrame, columnas_requeridas: list[str], nombre_hoja: str) -> None:
    faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en {nombre_hoja}: {', '.join(faltantes)}")


def leer_archivo(ruta: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    extension = ruta.suffix.lower()

    if extension in [".xlsx", ".xls"]:
        excel = pd.ExcelFile(ruta)

        if "Compras" not in excel.sheet_names:
            for nombre_hoja in excel.sheet_names:
                hoja_binance = pd.read_excel(ruta, sheet_name=nombre_hoja)
                if parece_export_binance(hoja_binance):
                    return convertir_binance_a_formato_interno(hoja_binance)
            raise ValueError("El Excel debe tener una hoja llamada 'Compras' o ser un export compatible de Binance.")

        compras = pd.read_excel(ruta, sheet_name="Compras")

        if "Ventas" in excel.sheet_names:
            ventas = pd.read_excel(ruta, sheet_name="Ventas")
        else:
            ventas = pd.DataFrame(columns=COLUMNAS_VENTAS)

    elif extension == ".csv":
        compras = pd.read_csv(ruta)
        ventas = pd.DataFrame(columns=COLUMNAS_VENTAS)
    else:
        raise ValueError("Formato no permitido. Usá CSV o Excel.")

    if not all(columna in compras.columns for columna in COLUMNAS_COMPRAS):
        if parece_export_binance(compras):
            compras, ventas = convertir_binance_a_formato_interno(compras)
        else:
            validar_columnas(compras, COLUMNAS_COMPRAS, "Compras")
    else:
        validar_columnas(compras, COLUMNAS_COMPRAS, "Compras")

    if not ventas.empty:
        validar_columnas(ventas, COLUMNAS_VENTAS, "Ventas")

    compras = convertir_columnas_compras(compras)
    ventas = convertir_columnas_ventas(ventas)

    return compras, ventas


def crear_resumen_por_moneda(compras: pd.DataFrame, ventas: pd.DataFrame) -> pd.DataFrame:
    resumen = []

    if compras.empty:
        return pd.DataFrame()

    for moneda in compras["Nombre"].dropna().unique():
        compras_moneda = compras[compras["Nombre"] == moneda].copy()
        compras_abiertas = compras_moneda[compras_moneda["Estado"] == "ABIERTA"].copy()
        compras_cerradas = compras_moneda[compras_moneda["Estado"] == "CERRADA"].copy()

        if ventas.empty:
            pnl_cerrado_total = 0.0
            dolares_vendidos = 0.0
        else:
            ventas_moneda = ventas[ventas["Nombre"] == moneda].copy()
            pnl_cerrado_total = ventas_moneda["PNL realizado"].sum()
            dolares_vendidos = ventas_moneda["Dólares vendidos"].sum()

        if compras_abiertas.empty:
            dolares_abiertos = 0.0
        else:
            compras_abiertas["Dólares abiertos"] = compras_abiertas.apply(
                lambda fila: fila["Dólares comprados"] * (fila["Cantidad restante"] / fila["Cantidad comprada"])
                if fila["Cantidad comprada"] != 0
                else 0.0,
                axis=1,
            )
            dolares_abiertos = compras_abiertas["Dólares abiertos"].sum()

        dolares_invertidos = compras_moneda["Dólares comprados"].sum()
        roi = (pnl_cerrado_total / dolares_invertidos * 100) if dolares_invertidos else 0.0

        resumen.append(
            {
                "Moneda": moneda,
                "Dólares invertidos": round(dolares_invertidos, 2),
                "Dólares vendidos": round(dolares_vendidos, 2),
                "Dólares abiertos": round(dolares_abiertos, 2),
                "PNL cerrado total": round(pnl_cerrado_total, 2),
                "ROI %": round(roi, 2),
                "Operaciones abiertas": int(len(compras_abiertas)),
                "Operaciones cerradas": int(len(compras_cerradas)),
            }
        )

    return pd.DataFrame(resumen).sort_values("PNL cerrado total", ascending=False)


def crear_metricas(compras: pd.DataFrame, ventas: pd.DataFrame, resumen: pd.DataFrame) -> dict:
    total_invertido = compras["Dólares comprados"].sum() if not compras.empty else 0.0
    total_vendido = ventas["Dólares vendidos"].sum() if not ventas.empty else 0.0
    pnl_total = ventas["PNL realizado"].sum() if not ventas.empty else 0.0
    roi_total = (pnl_total / total_invertido * 100) if total_invertido else 0.0

    return {
        "total_invertido": round(total_invertido, 2),
        "total_vendido": round(total_vendido, 2),
        "pnl_total": round(pnl_total, 2),
        "roi_total": round(roi_total, 2),
        "operaciones_abiertas": int((compras["Estado"] == "ABIERTA").sum()) if not compras.empty else 0,
        "operaciones_cerradas": int((compras["Estado"] == "CERRADA").sum()) if not compras.empty else 0,
        "monedas": int(resumen["Moneda"].nunique()) if not resumen.empty else 0,
    }


def limpiar_valor_json(valor):
    if pd.isna(valor):
        return ""
    if hasattr(valor, "strftime"):
        return valor.strftime("%d-%m-%Y")
    if isinstance(valor, float):
        return round(valor, 8)
    return valor


def dataframe_a_registros(df: pd.DataFrame) -> list[dict]:
    return [
        {columna: limpiar_valor_json(valor) for columna, valor in fila.items()}
        for fila in df.to_dict(orient="records")
    ]


def crear_detalle_por_moneda(compras: pd.DataFrame, ventas: pd.DataFrame, resumen: pd.DataFrame) -> dict:
    detalle = {}

    if resumen.empty:
        return detalle

    for fila_resumen in resumen.to_dict(orient="records"):
        moneda = fila_resumen["Moneda"]
        compras_moneda = compras[compras["Nombre"] == moneda].copy()
        ventas_moneda = ventas[ventas["Nombre"] == moneda].copy() if not ventas.empty else pd.DataFrame(columns=COLUMNAS_VENTAS)

        abiertas = compras_moneda[compras_moneda["Estado"] == "ABIERTA"].copy()
        cerradas = compras_moneda[compras_moneda["Estado"] == "CERRADA"].copy()

        mejor_trade = None
        peor_trade = None
        win_rate = 0.0

        if not ventas_moneda.empty:
            ventas_ordenadas = ventas_moneda.sort_values("PNL realizado", ascending=False)
            mejor_trade = dataframe_a_registros(ventas_ordenadas.head(1))[0]
            peor_trade = dataframe_a_registros(ventas_ordenadas.tail(1))[0]
            win_rate = round((ventas_moneda["PNL realizado"] > 0).mean() * 100, 2)

        cantidad_comprada = compras_moneda["Cantidad comprada"].sum() if not compras_moneda.empty else 0.0
        total_invertido = compras_moneda[COLUMNAS_COMPRAS[3]].sum() if not compras_moneda.empty else 0.0
        precio_promedio = round(total_invertido / cantidad_comprada, 8) if cantidad_comprada else 0.0

        detalle[moneda] = {
            "resumen": {clave: limpiar_valor_json(valor) for clave, valor in fila_resumen.items()},
            "abiertas": dataframe_a_registros(abiertas),
            "cerradas": dataframe_a_registros(cerradas),
            "ventas": dataframe_a_registros(ventas_moneda.sort_values("Fecha venta") if not ventas_moneda.empty else ventas_moneda),
            "mejor_trade": mejor_trade,
            "peor_trade": peor_trade,
            "metricas": {
                "operaciones_totales": int(len(compras_moneda) + len(ventas_moneda)),
                "ventas_realizadas": int(len(ventas_moneda)),
                "win_rate": win_rate,
                "precio_promedio_compra": precio_promedio,
                "cantidad_restante": round(compras_moneda["Cantidad restante"].sum(), 8) if not compras_moneda.empty else 0.0,
            },
        }

    return detalle


def grafico_o_vacio(fig) -> str:
    # Incluye Plotly dentro del HTML del gráfico para que funcione localmente
    # aunque el navegador no cargue el CDN externo.
    return fig.to_html(full_html=False, include_plotlyjs=True, config={"displayModeBar": False})


def crear_graficos(compras: pd.DataFrame, ventas: pd.DataFrame, resumen: pd.DataFrame) -> dict:
    graficos = {}

    if not resumen.empty:
        fig_torta = px.pie(
            resumen,
            names="Moneda",
            values="Dólares invertidos",
            title="Distribución del capital invertido por moneda",
            hole=0.35,
        )
        graficos["torta_inversion"] = grafico_o_vacio(fig_torta)

        fig_pnl = px.bar(
            resumen,
            x="Moneda",
            y="PNL cerrado total",
            title="PNL cerrado total por moneda",
            text="PNL cerrado total",
        )
        graficos["barras_pnl"] = grafico_o_vacio(fig_pnl)

        fig_roi = px.bar(
            resumen,
            x="Moneda",
            y="ROI %",
            title="ROI porcentual por moneda",
            text="ROI %",
        )
        graficos["barras_roi"] = grafico_o_vacio(fig_roi)

    if not compras.empty:
        estado = compras["Estado"].value_counts().reset_index()
        estado.columns = ["Estado", "Cantidad"]
        fig_estado = px.pie(
            estado,
            names="Estado",
            values="Cantidad",
            title="Operaciones abiertas vs cerradas",
            hole=0.35,
        )
        graficos["estado_operaciones"] = grafico_o_vacio(fig_estado)

    if not ventas.empty and "Fecha venta" in ventas.columns:
        ventas_timeline = ventas.copy()
        ventas_timeline["Fecha venta"] = pd.to_datetime(ventas_timeline["Fecha venta"], format="%d-%m-%Y", errors="coerce")
        ventas_timeline = ventas_timeline.dropna(subset=["Fecha venta"]).sort_values("Fecha venta")
        ventas_timeline["PNL acumulado"] = ventas_timeline["PNL realizado"].cumsum()

        if not ventas_timeline.empty:
            fig_linea = px.line(
                ventas_timeline,
                x="Fecha venta",
                y="PNL acumulado",
                markers=True,
                title="Evolución del PNL acumulado",
            )
            graficos["linea_pnl"] = grafico_o_vacio(fig_linea)

    return graficos


def guardar_reporte(resumen: pd.DataFrame, compras: pd.DataFrame, ventas: pd.DataFrame) -> Path:
    ruta_reporte = UPLOAD_FOLDER / "reporte_crypto_generado.xlsx"
    with pd.ExcelWriter(ruta_reporte, engine="openpyxl") as writer:
        resumen.to_excel(writer, sheet_name="Resumen por moneda", index=False)
        compras.to_excel(writer, sheet_name="Compras", index=False)
        ventas.to_excel(writer, sheet_name="Ventas", index=False)
    return ruta_reporte


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        archivo = request.files.get("archivo")

        if not archivo or archivo.filename == "":
            flash("Subí un archivo CSV o Excel.", "danger")
            return redirect(url_for("index"))

        if not extension_permitida(archivo.filename):
            flash("Formato no permitido. Usá .csv, .xlsx o .xls.", "danger")
            return redirect(url_for("index"))

        filename = secure_filename(archivo.filename)
        ruta = UPLOAD_FOLDER / filename
        archivo.save(ruta)

        try:
            compras, ventas = leer_archivo(ruta)
            resumen = crear_resumen_por_moneda(compras, ventas)
            metricas = crear_metricas(compras, ventas, resumen)
            graficos = crear_graficos(compras, ventas, resumen)
            detalle_monedas = crear_detalle_por_moneda(compras, ventas, resumen)
            guardar_reporte(resumen, compras, ventas)

            return render_template(
                "dashboard.html",
                filename=filename,
                metricas=metricas,
                graficos=graficos,
                detalle_monedas=detalle_monedas,
                resumen=resumen.to_dict(orient="records"),
                compras=compras.head(30).to_dict(orient="records"),
                ventas=ventas.head(30).to_dict(orient="records"),
            )

        except Exception as error:
            flash(str(error), "danger")
            return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/descargar-reporte")
def descargar_reporte():
    ruta_reporte = UPLOAD_FOLDER / "reporte_crypto_generado.xlsx"
    if not ruta_reporte.exists():
        flash("Primero tenés que generar un reporte.", "warning")
        return redirect(url_for("index"))
    return send_file(ruta_reporte, as_attachment=True, download_name="reporte_crypto_generado.xlsx")


if __name__ == "__main__":
    app.run(debug=True)
