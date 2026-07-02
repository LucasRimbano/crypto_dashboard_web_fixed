+Dashboard web para analizar operaciones de criptomonedas desde archivos CSV o Excel. La aplicacion procesa compras y ventas, calcula PNL, ROI, operaciones abiertas/cerradas y genera graficos interactivos con detalle por moneda.
+
+Proyecto creado con **Python, Flask, pandas, Plotly, Bootstrap, HTML, CSS y JavaScript**.
+
+## Caracteristicas
+
+- Carga de archivos `.xlsx`, `.xls` y `.csv`.
+- Lectura de reportes manuales con hojas `Compras` y `Ventas`.
+- Deteccion de exports compatibles de Binance Spot Trade History.
+- Conversion automatica de operaciones Binance al formato interno del dashboard.
+- Calculo de metricas principales:
+  - Total invertido.
+  - Total vendido.
+  - PNL total realizado.
+  - ROI total.
+  - Operaciones abiertas.
+  - Operaciones cerradas.
+  - Resumen por moneda.
+- Graficos interactivos con Plotly:
+  - Distribucion del capital invertido por moneda.
+  - PNL cerrado por moneda.
+  - ROI porcentual por moneda.
+  - Operaciones abiertas vs cerradas.
+  - Evolucion del PNL acumulado.
+- Detalle ampliado por moneda al hacer clic en graficos o filas.
+- Resumen automatico de rendimiento:
+  - Mejor trade.
+  - Peor perdida realizada.
+  - Mejor moneda por PNL.
+  - Moneda con peor rendimiento.
+  - Win rate global.
+  - Mejor ROI por moneda.
+- Descarga de reporte Excel generado.
+- Formulario de contacto para solicitar una version personalizada.
+
+## Vista general
+
+La app permite subir un archivo de operaciones y genera un dashboard con:
+
+- Tarjetas de metricas generales.
+- Graficos interactivos.
+- Tabla resumen por moneda.
+- Panel de detalle por moneda con operaciones abiertas, cerradas y ventas.
+- Boton para generar un resumen ejecutivo del rendimiento.
+
+## Formatos soportados
+
+### 1. Excel manual
+
+El archivo puede incluir una hoja obligatoria llamada `Compras` y una hoja opcional llamada `Ventas`.
+
+Columnas requeridas para `Compras`:
+
+```txt
+ID
+Nombre
+Fecha de compra
+Dolares comprados
+Precio de compra
+Cantidad comprada
+Cantidad vendida total
+Cantidad restante
+Estado
+```
+
+Columnas opcionales para `Ventas`:
+
+```txt
+ID venta
+ID compra
+Nombre
+Fecha venta
+Cantidad vendida
+Precio venta
+Dolares vendidos
+Costo proporcional
+PNL realizado
+```
+
+### 2. Export de Binance
+
+Tambien acepta CSV o Excel exportados desde Binance Spot Trade History con columnas como:
+
+```txt
+Date(UTC)
+Pair
+Side
+Price
+Executed
+Amount
+```
+
+La aplicacion detecta este formato y convierte las operaciones al modelo interno de compras y ventas.
+
+### 3. Reporte limpio
+
+Tambien puede trabajar con reportes ya limpiados con columnas como:
+
+```txt
+Fecha
+Par
+Lado
+Cantidad
+Precio
+Total_Cotizacion
+```
+
+## Instalacion
+
+1. Clonar el repositorio:
+
+```bash
+git clone https://github.com/tu-usuario/crypto-dashboard-web.git
+cd crypto-dashboard-web
+```
+
+2. Crear y activar un entorno virtual:
+
+```bash
+python -m venv .venv
+```
+
+En Windows:
+
+```bash
+.venv\Scripts\activate
+```
+
+En macOS/Linux:
+
+```bash
+source .venv/bin/activate
+```
+
+3. Instalar dependencias:
+
+```bash
+pip install -r requirements.txt
+```
+
+## Ejecutar el proyecto
+
+```bash
+python app.py
+```
+
+Luego abrir en el navegador:
+
+```txt
+http://127.0.0.1:5000
+```
+
+## Estructura del proyecto
+
+```txt
+crypto_dashboard_web_fixed/
+├── app.py
+├── requirements.txt
+├── README.md
+├── static/
+│   ├── css/
+│   │   └── style.css
+│   ├── img/
+│   │   ├── trading-dashboard-bg.png
+│   │   └── trading-charts-bg.png
+│   └── js/
+│       ├── animations.js
+│       ├── contact.js
+│       └── dashboard-detail.js
+├── templates/
+│   ├── base.html
+│   ├── dashboard.html
+│   └── index.html
+└── uploads/
+    └── .gitkeep
+```
+
+## Tecnologias
+
+- Python
+- Flask
+- pandas
+- openpyxl
+- Plotly
+- Bootstrap
+- HTML
+- CSS
+- JavaScript
+
+## Notas
+
+- Esta aplicacion esta pensada como dashboard local/demo.
+- Para produccion se recomienda cambiar `SECRET_KEY`, desactivar `debug=True` y usar un servidor WSGI como Gunicorn, Waitress o uWSGI.
+- Los archivos subidos se guardan en la carpeta `uploads/`.
+
+## Autor
+
+Creado por **Lucas Rimbano** para **tunegocioweb**.
+
