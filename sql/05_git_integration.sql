-- =====================================================
-- POD GROUP MANAGER - Snowflake Git Integration & Streamlit App
-- =====================================================
-- Pulls the app from a PRIVATE GitHub repo into Snowflake and creates the
-- Streamlit object. Run sql/01-04 first.
--
-- NOTE: secrets and external access integrations are normally managed in the
-- Snowflake-Deployment repo. The DDL below is the reference; create the PAT
-- secret there if that is your team's convention.

-- -----------------------------------------------------
-- 1. Secret + API integration for the private repo
-- -----------------------------------------------------
USE ROLE EXTERNAL_ACCESS_ADMIN;
USE DATABASE EXTERNAL_ACCESS;
CREATE SCHEMA IF NOT EXISTS GITHUB;
USE SCHEMA GITHUB;

-- GitHub PAT with read access to wnl-icb-analytics/pod-group-manager.
-- Replace the placeholder; do not commit a real token.
CREATE OR REPLACE SECRET pod_group_manager_git_secret
  TYPE = password
  USERNAME = '<github-username>'
  PASSWORD = '<github-personal-access-token>';

-- Dedicated integration for the private WNL repo (leaves the shared public
-- github_integration used by other apps untouched).
CREATE API INTEGRATION IF NOT EXISTS github_wnl_private_integration
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/wnl-icb-analytics')
  ALLOWED_AUTHENTICATION_SECRETS = (pod_group_manager_git_secret)
  ENABLED = TRUE;

CREATE OR REPLACE GIT REPOSITORY POD_GROUP_MANAGER_REPO
  API_INTEGRATION = github_wnl_private_integration
  GIT_CREDENTIALS = pod_group_manager_git_secret
  ORIGIN = 'https://github.com/wnl-icb-analytics/pod-group-manager.git';

ALTER GIT REPOSITORY POD_GROUP_MANAGER_REPO FETCH;

GRANT READ ON GIT REPOSITORY POD_GROUP_MANAGER_REPO TO ROLE ENGINEER;
GRANT WRITE ON GIT REPOSITORY POD_GROUP_MANAGER_REPO TO ROLE ENGINEER;
GRANT READ ON GIT REPOSITORY POD_GROUP_MANAGER_REPO TO ROLE ANALYST;

-- -----------------------------------------------------
-- 2. Create the Streamlit app from the repo
-- -----------------------------------------------------
USE ROLE ENGINEER;
USE DATABASE DATA_LAKE__NCL;
USE SCHEMA POD_GROUP_MANAGER;

CREATE OR REPLACE STREAMLIT POD_GROUP_MANAGER
  ROOT_LOCATION = '@EXTERNAL_ACCESS.GITHUB.POD_GROUP_MANAGER_REPO/branches/main'
  MAIN_FILE = '/streamlit_app.py'
  QUERY_WAREHOUSE = 'NCL_ANALYTICS_XS'
  COMMENT = 'POD Group Manager - assign and maintain POD group overview mappings';

GRANT USAGE ON STREAMLIT POD_GROUP_MANAGER TO ROLE ANALYST;

-- -----------------------------------------------------
-- 3. Maintenance
-- -----------------------------------------------------
-- Pull latest app changes after pushing to GitHub:
--   ALTER GIT REPOSITORY EXTERNAL_ACCESS.GITHUB.POD_GROUP_MANAGER_REPO FETCH;
