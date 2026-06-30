-- =====================================================
-- POD GROUP MANAGER - STORED PROCEDURES
-- =====================================================
-- All writes go through procedures so key-generation, option validation
-- and audit logging happen in one place.

USE ROLE ENGINEER;
USE SCHEMA DATA_LAKE__NCL.POD_GROUP_MANAGER;

-- -----------------------------------------------------
-- Create or update a single mapping.
-- Component fields are passed with real NULLs for missing values;
-- the legacy POD_LOOKUP key is derived here.
-- -----------------------------------------------------
CREATE OR REPLACE PROCEDURE UPSERT_POD_MAPPING(
    P_POINT  STRING,
    P_LOCAL  STRING,
    P_DESC   STRING,
    P_GROUP  STRING,
    P_ACTOR  STRING,
    P_NOTES  STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    v_lookup STRING;
    v_old    STRING;
    v_valid  INT;
BEGIN
    v_lookup := CONCAT(IFNULL(:P_POINT, '?'),
                       IFNULL(:P_LOCAL, '?'),
                       IFNULL(:P_DESC, '?'));

    -- Validate the chosen group is an active option
    SELECT COUNT(*) INTO :v_valid
    FROM POD_GROUP_OPTION
    WHERE pod_group_name = :P_GROUP AND is_active = TRUE;

    IF (v_valid = 0) THEN
        RETURN 'ERROR: invalid or inactive POD group ''' || :P_GROUP || '''';
    END IF;

    -- Capture existing value (if any) for the audit log
    SELECT MAX(pod_group_overview_master) INTO :v_old
    FROM POD_GROUP_MAPPING WHERE pod_lookup = :v_lookup;

    MERGE INTO POD_GROUP_MAPPING t
    USING (SELECT :v_lookup AS pod_lookup) s
    ON t.pod_lookup = s.pod_lookup
    WHEN MATCHED THEN UPDATE SET
        pod_group_overview_master = :P_GROUP,
        notes      = :P_NOTES,
        updated_by = :P_ACTOR,
        updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT (
        pod_lookup, point_of_delivery_code, local_point_of_delivery_code,
        local_point_of_delivery_description, pod_group_overview_master,
        notes, insertion_date, created_by, updated_by
    ) VALUES (
        :v_lookup, :P_POINT, :P_LOCAL, :P_DESC, :P_GROUP,
        :P_NOTES, CURRENT_DATE(), :P_ACTOR, :P_ACTOR
    );

    INSERT INTO POD_GROUP_MAPPING_CHANGES (pod_lookup, change_type, old_value, new_value, notes, changed_by)
    SELECT :v_lookup,
           IFF(:v_old IS NULL, 'CREATE', 'UPDATE'),
           :v_old, :P_GROUP, :P_NOTES, :P_ACTOR;

    RETURN 'SUCCESS: ' || IFF(:v_old IS NULL, 'created ', 'updated ') || :v_lookup;
END;
$$;

-- -----------------------------------------------------
-- Update the group on an existing mapping by its key (retrospective edit).
-- -----------------------------------------------------
CREATE OR REPLACE PROCEDURE UPDATE_POD_MAPPING_GROUP(
    P_LOOKUP STRING,
    P_GROUP  STRING,
    P_ACTOR  STRING,
    P_NOTES  STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    v_old   STRING;
    v_valid INT;
    v_exists INT;
BEGIN
    SELECT COUNT(*) INTO :v_valid
    FROM POD_GROUP_OPTION WHERE pod_group_name = :P_GROUP AND is_active = TRUE;
    IF (v_valid = 0) THEN
        RETURN 'ERROR: invalid or inactive POD group ''' || :P_GROUP || '''';
    END IF;

    SELECT COUNT(*), MAX(pod_group_overview_master) INTO :v_exists, :v_old
    FROM POD_GROUP_MAPPING WHERE pod_lookup = :P_LOOKUP;
    IF (v_exists = 0) THEN
        RETURN 'ERROR: no mapping for ''' || :P_LOOKUP || '''';
    END IF;

    UPDATE POD_GROUP_MAPPING
    SET pod_group_overview_master = :P_GROUP,
        old_pod_group_overview = :v_old,
        notes = :P_NOTES,
        updated_by = :P_ACTOR,
        updated_at = CURRENT_TIMESTAMP()
    WHERE pod_lookup = :P_LOOKUP;

    INSERT INTO POD_GROUP_MAPPING_CHANGES (pod_lookup, change_type, old_value, new_value, notes, changed_by)
    VALUES (:P_LOOKUP, 'UPDATE', :v_old, :P_GROUP, :P_NOTES, :P_ACTOR);

    RETURN 'SUCCESS: updated ' || :P_LOOKUP;
END;
$$;

-- -----------------------------------------------------
-- Delete a mapping by key.
-- -----------------------------------------------------
CREATE OR REPLACE PROCEDURE DELETE_POD_MAPPING(
    P_LOOKUP STRING,
    P_ACTOR  STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    v_old    STRING;
    v_exists INT;
BEGIN
    SELECT COUNT(*), MAX(pod_group_overview_master) INTO :v_exists, :v_old
    FROM POD_GROUP_MAPPING WHERE pod_lookup = :P_LOOKUP;
    IF (v_exists = 0) THEN
        RETURN 'ERROR: no mapping for ''' || :P_LOOKUP || '''';
    END IF;

    DELETE FROM POD_GROUP_MAPPING WHERE pod_lookup = :P_LOOKUP;

    INSERT INTO POD_GROUP_MAPPING_CHANGES (pod_lookup, change_type, old_value, new_value, notes, changed_by)
    VALUES (:P_LOOKUP, 'DELETE', :v_old, NULL, NULL, :P_ACTOR);

    RETURN 'SUCCESS: deleted ' || :P_LOOKUP;
END;
$$;

-- -----------------------------------------------------
-- Add or update a dropdown option.
-- -----------------------------------------------------
CREATE OR REPLACE PROCEDURE UPSERT_POD_OPTION(
    P_NAME   STRING,
    P_ORDER  INT,
    P_ACTIVE BOOLEAN,
    P_ACTOR  STRING
)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    MERGE INTO POD_GROUP_OPTION t
    USING (SELECT :P_NAME AS pod_group_name) s
    ON t.pod_group_name = s.pod_group_name
    WHEN MATCHED THEN UPDATE SET sort_order = :P_ORDER, is_active = :P_ACTIVE
    WHEN NOT MATCHED THEN INSERT (pod_group_name, sort_order, is_active, created_by)
        VALUES (:P_NAME, :P_ORDER, :P_ACTIVE, :P_ACTOR);
    RETURN 'SUCCESS: option ' || :P_NAME;
END;
$$;
