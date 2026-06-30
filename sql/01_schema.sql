-- =====================================================
-- POD GROUP MANAGER - SCHEMA & CONFIG TABLES
-- =====================================================
-- New schema is the source of truth for POD group overview mappings.
-- The legacy table DATA_LAKE__NCL.ANALYST_MANAGED.FA__MONTHLY_WNL_POD_GROUP_OVERVIEW
-- is never written to by this app; downstream repoints to V_POD_GROUP_OVERVIEW.

USE ROLE ENGINEER;
USE DATABASE DATA_LAKE__NCL;
CREATE SCHEMA IF NOT EXISTS POD_GROUP_MANAGER;
USE SCHEMA DATA_LAKE__NCL.POD_GROUP_MANAGER;

-- -----------------------------------------------------
-- Reference: valid POD group overview values (the dropdown)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS POD_GROUP_OPTION (
    pod_group_name STRING NOT NULL PRIMARY KEY,
    sort_order     INT,
    is_active      BOOLEAN DEFAULT TRUE,
    created_by     STRING DEFAULT CURRENT_USER(),
    created_at     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- -----------------------------------------------------
-- Reference: in-scope providers for unmapped detection
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS POD_GROUP_PROVIDER (
    provider_code STRING NOT NULL PRIMARY KEY,
    provider_name STRING,
    is_active     BOOLEAN DEFAULT TRUE,
    created_by    STRING DEFAULT CURRENT_USER(),
    created_at    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- -----------------------------------------------------
-- Master mapping table (source of truth)
-- Component fields stored with real NULLs. POD_LOOKUP is the legacy
-- concat key, maintained for backward-compatible downstream joins.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS POD_GROUP_MAPPING (
    pod_lookup                          STRING NOT NULL PRIMARY KEY,
    point_of_delivery_code              STRING,
    local_point_of_delivery_code        STRING,
    local_point_of_delivery_description STRING,
    pod_group_overview_master           STRING NOT NULL,
    old_pod_group_overview              STRING,
    notes                               STRING,
    insertion_date                      DATE DEFAULT CURRENT_DATE(),
    created_by                          STRING,
    created_at                          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_by                          STRING,
    updated_at                          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- -----------------------------------------------------
-- Change history (full audit trail of create/update/delete)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS POD_GROUP_MAPPING_CHANGES (
    change_id    NUMBER(38,0) IDENTITY(1,1) PRIMARY KEY,
    pod_lookup   STRING NOT NULL,
    change_type  STRING NOT NULL,            -- CREATE | UPDATE | DELETE
    old_value    STRING,                     -- previous pod_group_overview_master
    new_value    STRING,                     -- new pod_group_overview_master
    notes        STRING,
    changed_by   STRING,
    changed_at   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- -----------------------------------------------------
-- Comments
-- -----------------------------------------------------
COMMENT ON TABLE POD_GROUP_OPTION          IS 'Valid POD group overview values shown in the app dropdown';
COMMENT ON TABLE POD_GROUP_PROVIDER        IS 'In-scope provider codes used to detect unmapped POD combinations';
COMMENT ON TABLE POD_GROUP_MAPPING         IS 'Master POD group overview mappings (source of truth)';
COMMENT ON TABLE POD_GROUP_MAPPING_CHANGES IS 'Audit history of mapping create/update/delete actions';

COMMENT ON COLUMN POD_GROUP_MAPPING.pod_lookup IS 'Legacy concat key CONCAT(IFNULL(pod,?),IFNULL(local,?),IFNULL(desc,?)) - kept for downstream join compatibility';
COMMENT ON COLUMN POD_GROUP_MAPPING.pod_group_overview_master IS 'Assigned POD group overview (FK to POD_GROUP_OPTION.pod_group_name)';

-- -----------------------------------------------------
-- Seed: 18 valid POD group values (Sheet2 of the source workbook)
-- -----------------------------------------------------
MERGE INTO POD_GROUP_OPTION t
USING (
    SELECT * FROM VALUES
        ('Accident and Emergency', 1),
        ('Advice and Guidance', 2),
        ('Ambulatory Care', 3),
        ('CQUIN', 4),
        ('Chemo', 5),
        ('Community', 6),
        ('Critical Care', 7),
        ('Diagnostic Imaging', 8),
        ('Drugs and Devices', 9),
        ('Elective', 10),
        ('Maternity', 11),
        ('Non-elective', 12),
        ('Other', 13),
        ('Outpatients', 14),
        ('Patient Transport Service', 15),
        ('Regular Attenders', 16),
        ('Same Day Emergency Care', 17),
        ('Therapies', 18)
    AS s(pod_group_name, sort_order)
) s
ON t.pod_group_name = s.pod_group_name
WHEN NOT MATCHED THEN INSERT (pod_group_name, sort_order) VALUES (s.pod_group_name, s.sort_order);

-- -----------------------------------------------------
-- Seed: in-scope acute providers (from the source detection query)
-- -----------------------------------------------------
MERGE INTO POD_GROUP_PROVIDER t
USING (
    SELECT * FROM VALUES
        ('RAP'),('RAL'),('RKE'),('RRV'),('RAN'),('RP4'),
        ('RP6'),('R1K'),('RYJ'),('RQM'),('RAS')
    AS s(provider_code)
) s
ON t.provider_code = s.provider_code
WHEN NOT MATCHED THEN INSERT (provider_code) VALUES (s.provider_code);
