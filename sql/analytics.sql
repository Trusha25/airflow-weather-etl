-- 1. Average / max temperature by city
SELECT c.city_name, ROUND(AVG(f.temperature_c),1) AS avg_temp, MAX(f.temperature_c) AS max_temp
FROM fact_weather f JOIN dim_city c USING (city_id)
GROUP BY c.city_name ORDER BY avg_temp DESC;

-- 2. Hottest hour for each city (window function)
SELECT city_name, ts, temperature_c FROM (
  SELECT c.city_name, f.ts, f.temperature_c,
         RANK() OVER (PARTITION BY c.city_name ORDER BY f.temperature_c DESC) AS rnk
  FROM fact_weather f JOIN dim_city c USING (city_id)
) t WHERE rnk = 1;

-- 3. Daily rainfall per city
SELECT d.full_date, c.city_name, ROUND(SUM(f.precipitation_mm),1) AS rain_mm
FROM fact_weather f
JOIN dim_city c USING (city_id) JOIN dim_date d USING (date_key)
GROUP BY d.full_date, c.city_name ORDER BY d.full_date, rain_mm DESC;

-- 4. Weekday vs weekend humidity
SELECT d.is_weekend, ROUND(AVG(f.humidity_pct),1) AS avg_humidity
FROM fact_weather f JOIN dim_date d USING (date_key) GROUP BY d.is_weekend;

-- 5. 3-hour moving average temperature (Pune)
SELECT f.ts, f.temperature_c,
       ROUND(AVG(f.temperature_c) OVER (ORDER BY f.ts ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),2) AS moving_avg_3h
FROM fact_weather f JOIN dim_city c USING (city_id)
WHERE c.city_name = 'Pune' ORDER BY f.ts;
