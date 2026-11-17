"""
analisis_clima.py
-----------------
Análisis de una serie temporal de clima (Seattle, 2012-2015) con DuckDB.

Enfoque de motor embebido: DuckDB consulta el archivo CSV DIRECTAMENTE, en una
conexión en memoria (no se crea ningún archivo binario de base de datos).

Ejecuta varias consultas analíticas y reporta el tiempo de respuesta de cada una.

Uso:
    python analisis_clima.py
"""
import time
import duckdb

CSV = "data/weather_seattle.csv"


def correr(con, titulo: str, sql: str):
    """Ejecuta una consulta, mide su tiempo de respuesta y muestra el resultado."""
    t0 = time.perf_counter()
    df = con.execute(sql).df()
    ms = (time.perf_counter() - t0) * 1000
    print(f"\n### {titulo}  ({ms:.1f} ms)")
    print(df.to_string(index=False))
    return df


def main():
    # Conexión EN MEMORIA -> no genera archivos .duckdb/.db (motor embebido)
    con = duckdb.connect(database=":memory:")

    # --- Registro del archivo como tabla/vista virtual (consulta directa sobre CSV) ---
    con.execute(f"""
        CREATE VIEW clima_raw AS
        SELECT * FROM read_csv_auto('{CSV}', header=true);
    """)

    # --- Limpieza básica: manejo de nulos en temperaturas ---
    # Reporte de calidad: cuántas filas tienen temperatura nula.
    con.execute("""
        CREATE VIEW clima AS
        SELECT
            CAST(date AS DATE)            AS fecha,
            precipitation,
            temp_max,
            temp_min,
            wind,
            weather,
            CASE
                WHEN month(CAST(date AS DATE)) IN (12, 1, 2) THEN 'Invierno'
                WHEN month(CAST(date AS DATE)) IN (3, 4, 5)  THEN 'Primavera'
                WHEN month(CAST(date AS DATE)) IN (6, 7, 8)  THEN 'Verano'
                ELSE 'Otoño'
            END                           AS estacion
        FROM clima_raw
        -- Se descartan filas sin temperatura (núcleo del análisis).
        WHERE temp_max IS NOT NULL AND temp_min IS NOT NULL;
    """)

    print("=== Análisis de clima con DuckDB (Seattle 2012-2015) ===")

    correr(con, "Control de calidad: filas totales y nulos de temperatura", """
        SELECT
            (SELECT count(*) FROM clima_raw)                                   AS filas_totales,
            (SELECT count(*) FROM clima_raw WHERE temp_max IS NULL)            AS nulos_temp_max,
            (SELECT count(*) FROM clima_raw WHERE temp_min IS NULL)            AS nulos_temp_min,
            (SELECT count(*) FROM clima)                                       AS filas_validas;
    """)

    correr(con, "1) Promedios mensuales de temperatura y precipitación", """
        SELECT
            year(fecha)                      AS anio,
            month(fecha)                     AS mes,
            round(avg(temp_max), 1)          AS temp_max_prom,
            round(avg(temp_min), 1)          AS temp_min_prom,
            round(avg(precipitation), 1)     AS precip_prom
        FROM clima
        GROUP BY anio, mes
        ORDER BY anio, mes
        LIMIT 12;
    """)

    correr(con, "2) Máximo histórico de temperatura por estación del año", """
        SELECT
            estacion,
            max(temp_max)                                        AS temp_max_record,
            arg_max(fecha, temp_max)                             AS fecha_record,
            round(avg(temp_max), 1)                              AS temp_max_prom
        FROM clima
        GROUP BY estacion
        ORDER BY temp_max_record DESC;
    """)

    correr(con, "3) Conteo de días por tipo de clima (con porcentaje)", """
        SELECT
            weather                                              AS tipo_clima,
            count(*)                                             AS dias,
            round(100.0 * count(*) / sum(count(*)) OVER (), 1)   AS porcentaje
        FROM clima
        GROUP BY weather
        ORDER BY dias DESC;
    """)

    correr(con, "4) Filtro complejo: días de lluvia intensa y viento fuerte", """
        SELECT
            year(fecha)                      AS anio,
            count(*)                         AS dias_tormenta,
            round(avg(precipitation), 1)     AS precip_prom,
            round(max(wind), 1)              AS viento_max
        FROM clima
        WHERE weather = 'rain'
          AND precipitation > 10
          AND wind > 4
        GROUP BY anio
        ORDER BY anio;
    """)

    correr(con, "5) Top 5 de días más calurosos del período", """
        SELECT fecha, temp_max, temp_min, weather
        FROM clima
        ORDER BY temp_max DESC
        LIMIT 5;
    """)

    con.close()
    print("\n=== Análisis finalizado ===")


if __name__ == "__main__":
    main()
