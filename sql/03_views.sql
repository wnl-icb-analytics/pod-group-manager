-- =====================================================
-- POD GROUP MANAGER - VIEWS
-- =====================================================

USE ROLE ENGINEER;
USE SCHEMA DATA_LAKE__NCL.POD_GROUP_MANAGER;

-- -----------------------------------------------------
-- Backward-compatible view: identical shape to the legacy
-- ANALYST_MANAGED.FA__MONTHLY_WNL_POD_GROUP_OVERVIEW table.
-- -----------------------------------------------------
CREATE OR REPLACE VIEW V_POD_GROUP_OVERVIEW AS
SELECT
    pod_lookup                                          AS POD_LOOKUP,
    IFNULL(point_of_delivery_code, '?')                 AS POINT_OF_DELIVERY_CODE,
    IFNULL(local_point_of_delivery_code, '?')           AS LOCAL_POINT_OF_DELIVERY_CODE,
    IFNULL(local_point_of_delivery_description, '?')     AS LOCAL_POINT_OF_DELIVERY_DESCRIPTION,
    old_pod_group_overview                              AS OLD_POD_GROUP_OVERVIEW,
    pod_group_overview_master                          AS POD_GROUP_OVERVIEW_MASTER,
    insertion_date                                     AS INSERTION_DATE
FROM POD_GROUP_MAPPING;

-- -----------------------------------------------------
-- Latest submitted file per in-scope provider (shared by the views below).
-- -----------------------------------------------------
CREATE OR REPLACE VIEW V_LATEST_FILES AS
SELECT
    "FINANCIAL YEAR"                              AS FINANCIAL_YEAR,
    "ORGANISATION IDENTIFIER (CODE OF PROVIDER)"  AS PROVIDER_CODE,
    MAX("FileID")                                 AS FILE_ID
FROM DATA_LAKE.SERVICES_DATA."LSACM_LocalStandardAggregateContractMonitoring"
WHERE "ORGANISATION IDENTIFIER (CODE OF PROVIDER)" IN (
    SELECT provider_code FROM POD_GROUP_PROVIDER WHERE is_active
)
GROUP BY 1, 2;

-- -----------------------------------------------------
-- Unmapped detection: combinations in the latest file per provider that have
-- no entry in the master mapping yet, with a volume signal.
-- -----------------------------------------------------
CREATE OR REPLACE VIEW V_UNMAPPED_PODS AS
WITH source AS (
    SELECT
        lf.FINANCIAL_YEAR AS financial_year,
        lf.PROVIDER_CODE  AS provider_code,
        L.POINT_OF_DELIVERY_CODE,
        L.LOCAL_POINT_OF_DELIVERY_CODE,
        L.LOCAL_POINT_OF_DELIVERY_DESCRIPTION,
        CONCAT(
            IFNULL(L.POINT_OF_DELIVERY_CODE, '?'),
            IFNULL(L.LOCAL_POINT_OF_DELIVERY_CODE, '?'),
            IFNULL(L.LOCAL_POINT_OF_DELIVERY_DESCRIPTION, '?')
        ) AS pod_lookup
    FROM STAGING.LSACM.STG_LSACM L
    JOIN V_LATEST_FILES lf ON L.META_FILE_ID = lf.FILE_ID
)
SELECT
    s.financial_year                          AS FINANCIAL_YEAR,
    s.pod_lookup                              AS POD_LOOKUP,
    s.POINT_OF_DELIVERY_CODE,
    s.LOCAL_POINT_OF_DELIVERY_CODE,
    s.LOCAL_POINT_OF_DELIVERY_DESCRIPTION,
    COUNT(*)                                  AS RECORD_COUNT,
    COUNT(DISTINCT s.provider_code)           AS PROVIDER_COUNT,
    LISTAGG(DISTINCT s.provider_code, ', ')
        WITHIN GROUP (ORDER BY s.provider_code) AS PROVIDERS
FROM source s
LEFT JOIN POD_GROUP_MAPPING m ON s.pod_lookup = m.pod_lookup
WHERE m.pod_lookup IS NULL
GROUP BY 1, 2, 3, 4, 5
ORDER BY RECORD_COUNT DESC, POD_LOOKUP;

-- -----------------------------------------------------
-- Activity by POD group: latest file per provider, each combination resolved
-- to its POD group (or '(unmapped)'), with actual/planned activity and price.
-- This is the fact table the Analytics page aggregates.
-- -----------------------------------------------------
CREATE OR REPLACE VIEW V_POD_ACTIVITY AS
WITH source AS (
    SELECT
        lf.FINANCIAL_YEAR AS financial_year,
        lf.PROVIDER_CODE  AS provider_code,
        CONCAT(
            IFNULL(L.POINT_OF_DELIVERY_CODE, '?'),
            IFNULL(L.LOCAL_POINT_OF_DELIVERY_CODE, '?'),
            IFNULL(L.LOCAL_POINT_OF_DELIVERY_DESCRIPTION, '?')
        ) AS pod_lookup,
        L.DV_ACTUAL_ACTIVITY    AS actual_activity,
        L.DV_ACTUAL_PRICE       AS actual_price,
        L.DV_PLANNED_ACTIVITY   AS planned_activity,
        L.DV_PLANNED_PRICE      AS planned_price
    FROM STAGING.LSACM.STG_LSACM L
    JOIN V_LATEST_FILES lf ON L.META_FILE_ID = lf.FILE_ID
)
SELECT
    s.financial_year                              AS FINANCIAL_YEAR,
    s.provider_code                               AS PROVIDER_CODE,
    COALESCE(m.pod_group_overview_master, '(unmapped)') AS POD_GROUP,
    IFF(m.pod_lookup IS NOT NULL, TRUE, FALSE)    AS IS_MAPPED,
    COUNT(*)                                      AS RECORD_COUNT,
    SUM(s.actual_activity)                        AS ACTUAL_ACTIVITY,
    SUM(s.actual_price)                           AS ACTUAL_PRICE,
    SUM(s.planned_activity)                       AS PLANNED_ACTIVITY,
    SUM(s.planned_price)                          AS PLANNED_PRICE
FROM source s
LEFT JOIN POD_GROUP_MAPPING m ON s.pod_lookup = m.pod_lookup
GROUP BY 1, 2, 3, 4;
