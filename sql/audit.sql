-- Source sample: one released user row; assignment is not actual exposure.
SELECT treatment, count(*) AS users, sum(conversion) AS conversions,
       avg(conversion) AS conversion_rate, avg(visit) AS visit_rate,
       avg(exposure) AS exposure_rate
FROM sample
GROUP BY treatment
ORDER BY treatment;
