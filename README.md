Crypto Dashboard Web
Aplicación web desarrollada con Python, Flask, pandas, Bootstrap y Plotly para analizar operaciones de criptomonedas desde archivos CSV o Excel.

La app permite subir un archivo con operaciones, procesar los datos automáticamente y generar un dashboard con métricas, tablas y gráficos interactivos.

Funcionalidades
Carga de archivos .xlsx, .xls o .csv.
Lectura de hojas Compras y Ventas desde Excel.
DetecciÃ³n automÃ¡tica de exports de Binance Spot Trade History.
Cálculo de:
Total invertido.
Total vendido.
PNL total realizado.
ROI total.
Operaciones abiertas.
Operaciones cerradas.
Resumen por moneda.
Gráficos interactivos:
Distribución de inversión por moneda.
PNL cerrado por moneda.
ROI por moneda.
Operaciones abiertas vs cerradas.
Evolución del PNL acumulado.
Descarga de reporte Excel generado.
Estructura esperada del Excel
La app acepta dos caminos:

Un Excel manual con una hoja llamada Compras.
Un CSV o Excel exportado desde Binance Spot Trade History con columnas como Date(UTC), Pair, Side, Price, Executed y Amount.
Un reporte ya limpiado con una hoja Datos limpios y columnas como Fecha, Par, Lado, Cantidad, Precio y Total_Cotizacion.
Si detecta Binance, la app convierte automÃ¡ticamente las operaciones al formato interno de compras y ventas.

Para el formato manual, el archivo Excel debe tener una hoja llamada Compras con estas columnas:

ID
Nombre
Fecha de compra
Dólares comprados
Precio de compra
Cantidad comprada
Cantidad vendida total
Cantidad restante
Estado
Opcionalmente puede tener una hoja llamada Ventas con estas columnas:

ID venta
ID compra
Nombre
Fecha venta
Cantidad vendida
Precio venta
Dólares vendidos
Costo proporcional
PNL realizado
Instalación
pip install -r requirements.txt
Ejecutar el proyecto
python app.py
Luego abrir en el navegador:

http://127.0.0.1:5000
Tecnologías usadas
Python
Flask
pandas
openpyxl
Plotly
Bootstrap
HTML
CSS
Autor
Creado por Lucas Rimbano para tunegocioweb.
