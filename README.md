# Pre-entrega · Análisis de Datos Meteorológicos con DuckDB

**Curso:** Data Science II — Coderhouse

Entorno analítico ligero con **DuckDB** para consultar una serie temporal de clima
**directamente sobre un archivo CSV**, sin cargar nada en una base de datos tradicional
y sin generar archivos binarios de base de datos (motor embebido, conexión en memoria).

## Dataset

**Seattle Weather (2012–2015)** — datos diarios derivados de NOAA, distribuidos con
el proyecto `vega-datasets`.

- 1.461 días (2012-01-01 a 2015-12-31), 6 columnas: `date`, `precipitation`,
  `temp_max`, `temp_min`, `wind`, `weather`.
- Fuente: https://github.com/vega/vega-datasets (`data/seattle-weather.csv`).
- El CSV se incluye en `data/weather_seattle.csv` para que el análisis sea reproducible.

## Estructura

```
preentrega6-duckdb-clima/
├── analisis_clima.py        # script principal (Python + DuckDB), mide tiempos
├── consultas.sql            # las mismas consultas en SQL puro (CLI de DuckDB)
├── data/
│   └── weather_seattle.csv  # dataset
├── requirements.txt
├── .gitignore
└── README.md
```

## Cómo ejecutar

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Opción A — script de Python (recomendada, imprime resultados y tiempos):
python analisis_clima.py

# Opción B — SQL puro con la CLI de DuckDB:
duckdb < consultas.sql
```

## Enfoque técnico

- **Consulta directa sobre el archivo:** `read_csv_auto('data/weather_seattle.csv')`
  registra el CSV como vista virtual; DuckDB lo lee sin paso de importación previo.
- **Motor embebido:** la conexión es `:memory:`, por lo que **no se crea ningún
  archivo `.duckdb`/`.db`** (además están en el `.gitignore`).
- **Limpieza de nulos en temperaturas:** la vista `clima` filtra filas con `temp_max`
  o `temp_min` nulas, y el script reporta el conteo de nulos. *Este dataset está
  completo (0 nulos), por lo que el filtro actúa por robustez.*

## Consultas implementadas

1. **Promedios mensuales** de temperatura máx/mín y precipitación.
2. **Máximo histórico de temperatura por estación del año** (al ser una única
   localidad, "estación" se interpreta como estación del año: invierno/primavera/
   verano/otoño).
3. **Conteo de días por tipo de clima** con su porcentaje (window function).
4. **Filtro complejo**: días de lluvia intensa (`precipitation > 10`) y viento fuerte
   (`wind > 4`), agregados por año.
5. **Top 5 de días más calurosos** del período.

## Hallazgos principales

- **Estacionalidad marcada:** la temperatura máxima promedio va de ~7 °C en enero a
  ~26 °C en agosto.
- **Récord histórico:** 35.6 °C el **11-ago-2014** (verano). El invierno nunca supera
  los ~19 °C.
- **Clima dominante:** `sun` 48.9 % de los días y `fog` 28.1 %; la lluvia aparece en
  el 17.7 %, y la nieve es marginal (1.6 %).
- **Tormentas (lluvia intensa + viento):** 13 días en 2012, descendiendo en los años
  siguientes (3 en 2013, 2 en 2015).

## Tiempos de respuesta

Sobre 1.461 filas, en memoria (los valores varían según la máquina):

| Consulta | Tiempo aprox. |
|----------|---------------|
| Control de calidad (incluye la **primera lectura** del CSV) | ~530 ms |
| Promedios mensuales | ~70 ms |
| Máximo por estación | ~90 ms |
| Conteo por tipo de clima | ~95 ms |
| Filtro complejo | ~65 ms |
| Top 5 más calurosos | ~65 ms |

La primera consulta concentra el costo de parsear el CSV; una vez leído, cada consulta
analítica resuelve en decenas de milisegundos, lo que ilustra la velocidad de DuckDB
para análisis sobre archivos sin servidor ni importación previa.

## Librerías

| Librería | Uso                                        |
|----------|--------------------------------------------|
| duckdb   | motor analítico embebido, consulta el CSV  |
| pandas   | mostrar los resultados de cada consulta    |
