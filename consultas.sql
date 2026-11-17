-- consultas.sql
-- Análisis de clima con DuckDB consultando el CSV DIRECTAMENTE.
-- Ejecutar con la CLI de DuckDB:   duckdb < consultas.sql
-- (conexión en memoria: no se crea ningún archivo binario de base de datos)

-- Vista virtual sobre el archivo CSV + estación del año
CREATE VIEW clima AS
SELECT
    CAST(date AS DATE) AS fecha,
    precipitation, temp_max, temp_min, wind, weather,
    CASE
        WHEN month(CAST(date AS DATE)) IN (12,1,2) THEN 'Invierno'
        WHEN month(CAST(date AS DATE)) IN (3,4,5)  THEN 'Primavera'
        WHEN month(CAST(date AS DATE)) IN (6,7,8)  THEN 'Verano'
        ELSE 'Otoño'
    END AS estacion
FROM read_csv_auto('data/weather_seattle.csv', header=true)
WHERE temp_max IS NOT NULL AND temp_min IS NOT NULL;  -- manejo de nulos

-- 1) Promedios mensuales
SELECT year(fecha) AS anio, month(fecha) AS mes,
       round(avg(temp_max),1) AS temp_max_prom,
       round(avg(temp_min),1) AS temp_min_prom,
       round(avg(precipitation),1) AS precip_prom
FROM clima GROUP BY anio, mes ORDER BY anio, mes;

-- 2) Máximo histórico por estación del año
SELECT estacion, max(temp_max) AS temp_max_record,
       arg_max(fecha, temp_max) AS fecha_record
FROM clima GROUP BY estacion ORDER BY temp_max_record DESC;

-- 3) Conteo de días por tipo de clima
SELECT weather AS tipo_clima, count(*) AS dias,
       round(100.0*count(*)/sum(count(*)) OVER (),1) AS porcentaje
FROM clima GROUP BY weather ORDER BY dias DESC;

-- 4) Filtro complejo: días de lluvia intensa y viento fuerte
SELECT year(fecha) AS anio, count(*) AS dias_tormenta,
       round(avg(precipitation),1) AS precip_prom, round(max(wind),1) AS viento_max
FROM clima
WHERE weather = 'rain' AND precipitation > 10 AND wind > 4
GROUP BY anio ORDER BY anio;
