-- =====================================================
-- POD GROUP MANAGER - ONE-TIME SEED FROM LEGACY TABLE
-- =====================================================
-- Read-only on ANALYST_MANAGED. Copies current mappings into the new master.
-- Keeps the legacy POD_LOOKUP verbatim (downstream join parity) but reverses
-- the '?' null-fill back to real NULLs on the component fields.
-- Safe to re-run: only inserts keys not already present.

USE ROLE ENGINEER;
USE SCHEMA DATA_LAKE__NCL.POD_GROUP_MANAGER;

MERGE INTO POD_GROUP_MAPPING t
USING (
    SELECT
        POD_LOOKUP                                          AS pod_lookup,
        NULLIF(POINT_OF_DELIVERY_CODE, '?')                 AS point_of_delivery_code,
        NULLIF(LOCAL_POINT_OF_DELIVERY_CODE, '?')           AS local_point_of_delivery_code,
        NULLIF(LOCAL_POINT_OF_DELIVERY_DESCRIPTION, '?')    AS local_point_of_delivery_description,
        POD_GROUP_OVERVIEW_MASTER                           AS pod_group_overview_master,
        OLD_POD_GROUP_OVERVIEW                              AS old_pod_group_overview,
        INSERTION_DATE                                      AS insertion_date
    FROM DATA_LAKE__NCL.ANALYST_MANAGED.FA__MONTHLY_WNL_POD_GROUP_OVERVIEW
    -- de-dupe defensively: keep the most recent row per key
    QUALIFY ROW_NUMBER() OVER (PARTITION BY POD_LOOKUP ORDER BY INSERTION_DATE DESC NULLS LAST) = 1
) s
ON t.pod_lookup = s.pod_lookup
WHEN NOT MATCHED THEN INSERT (
    pod_lookup, point_of_delivery_code, local_point_of_delivery_code,
    local_point_of_delivery_description, pod_group_overview_master,
    old_pod_group_overview, insertion_date, created_by, created_at, updated_by, updated_at
) VALUES (
    s.pod_lookup, s.point_of_delivery_code, s.local_point_of_delivery_code,
    s.local_point_of_delivery_description, s.pod_group_overview_master,
    s.old_pod_group_overview, s.insertion_date,
    'SEED:ANALYST_MANAGED', s.insertion_date::TIMESTAMP_NTZ,
    'SEED:ANALYST_MANAGED', s.insertion_date::TIMESTAMP_NTZ
);

-- Sanity check
SELECT COUNT(*) AS seeded_rows FROM POD_GROUP_MAPPING;
