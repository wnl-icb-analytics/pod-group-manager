-- =====================================================
-- POD GROUP MANAGER - VIEWS
-- =====================================================

USE ROLE ENGINEER;
USE SCHEMA DATA_LAKE__NCL.POD_GROUP_MANAGER;

-- -----------------------------------------------------
-- Backward-compatible view: identical shape to the legacy
-- ANALYST_MANAGED.FA__MONTHLY_WNL_POD_GROUP_OVERVIEW table.
-- Downstream reporting repoints here. POD_LOOKUP and the '?'-filled
-- component columns are reproduced exactly so existing joins are unchanged.
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
-- Unmapped detection: combinations present in the latest file per
-- in-scope provider that have no entry in the master mapping yet.
-- FINANCIAL_YEAR is exposed as a column so the app can filter by month/year.
-- RECORD_COUNT / PROVIDER_COUNT give a volume signal for prioritisation.
-- Mirrors the latest-file-per-provider logic of the original detection query.
-- -----------------------------------------------------
CREATE OR REPLACE VIEW V_UNMAPPED_PODS AS
WITH latest_files AS (
    SELECT
        "FINANCIAL YEAR"                              AS financial_year,
        "ORGANISATION IDENTIFIER (CODE OF PROVIDER)"  AS provider_code,
        MAX("FileID")                                 AS file_id
    FROM DATA_LAKE.SERVICES_DATA."LSACM_LocalStandardAggregateContractMonitoring"
    WHERE "ORGANISATION IDENTIFIER (CODE OF PROVIDER)" IN (
        SELECT provider_code FROM POD_GROUP_PROVIDER WHERE is_active
    )
    GROUP BY 1, 2
),
source AS (
    SELECT
        lf.financial_year,
        lf.provider_code,
        L.POINT_OF_DELIVERY_CODE,
        L.LOCAL_POINT_OF_DELIVERY_CODE,
        L.LOCAL_POINT_OF_DELIVERY_DESCRIPTION,
        CONCAT(
            IFNULL(L.POINT_OF_DELIVERY_CODE, '?'),
            IFNULL(L.LOCAL_POINT_OF_DELIVERY_CODE, '?'),
            IFNULL(L.LOCAL_POINT_OF_DELIVERY_DESCRIPTION, '?')
        ) AS pod_lookup
    FROM DATA_LAKE.SDL.LSACM L
    JOIN latest_files lf ON L.META_FILE_ID = lf.file_id
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
