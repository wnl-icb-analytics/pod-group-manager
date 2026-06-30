-- =====================================================
-- POD GROUP MANAGER - Snowflake Git Integration & Streamlit App
-- =====================================================
-- Pulls the app from GitHub into Snowflake and creates the Streamlit object.
-- Run sql/01-04 first.
--
-- Reuses the existing org-wide integration API__GITHUB__WNL_ICB_ANALYTICS
-- (Snowflake GitHub App auth, no per-repo secret) - the same pattern as
-- SNOMED_CLUSTER_MANAGER_REPO.

-- -----------------------------------------------------
-- 1. Git repository
-- -----------------------------------------------------
USE ROLE EXTERNAL_ACCESS_ADMIN;
USE DATABASE EXTERNAL_ACCESS;
USE SCHEMA GITHUB;

CREATE OR REPLACE GIT REPOSITORY POD_GROUP_MANAGER_REPO
  API_INTEGRATION = API__GITHUB__WNL_ICB_ANALYTICS
  ORIGIN = 'https://github.com/wnl-icb-analytics/pod-group-manager.git';

ALTER GIT REPOSITORY POD_GROUP_MANAGER_REPO FETCH;

GRANT READ  ON GIT REPOSITORY POD_GROUP_MANAGER_REPO TO ROLE ENGINEER;
GRANT WRITE ON GIT REPOSITORY POD_GROUP_MANAGER_REPO TO ROLE ENGINEER;
GRANT READ  ON GIT REPOSITORY POD_GROUP_MANAGER_REPO TO ROLE ANALYST;

-- -----------------------------------------------------
-- 2. Create the Streamlit app from the repo
-- -----------------------------------------------------
USE ROLE ENGINEER;
USE DATABASE DATA_LAKE__NCL;
USE SCHEMA POD_GROUP_MANAGER;

-- vNext / container-runtime Streamlit: use FROM (not ROOT_LOCATION) and a
-- MAIN_FILE with no leading slash. ROOT_LOCATION is rejected on this account.
CREATE OR REPLACE STREAMLIT POD_GROUP_MANAGER
  FROM '@EXTERNAL_ACCESS.GITHUB.POD_GROUP_MANAGER_REPO/branches/main'
  MAIN_FILE = 'streamlit_app.py'
  QUERY_WAREHOUSE = 'NCL_ANALYTICS_XS'
  TITLE = 'POD Group Manager'
  COMMENT = 'POD Group Manager - assign and maintain POD group overview mappings';

GRANT USAGE ON STREAMLIT POD_GROUP_MANAGER TO ROLE ANALYST;

-- -----------------------------------------------------
-- 3. Maintenance
-- -----------------------------------------------------
-- Pull latest app changes after pushing to GitHub: fetch the repo, then add a
-- new version to the Streamlit from the branch tip.
--   ALTER GIT REPOSITORY EXTERNAL_ACCESS.GITHUB.POD_GROUP_MANAGER_REPO FETCH;
--   ALTER STREAMLIT DATA_LAKE__NCL.POD_GROUP_MANAGER.POD_GROUP_MANAGER
--     ADD VERSION FROM '@EXTERNAL_ACCESS.GITHUB.POD_GROUP_MANAGER_REPO/branches/main';
