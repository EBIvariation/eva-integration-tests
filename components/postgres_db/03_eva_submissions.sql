-- Connect to the database
\c metadata_db

GRANT CREATE ON DATABASE metadata_db TO metadata_db_user;

--- schema (eva_submissions)
CREATE SCHEMA eva_submissions AUTHORIZATION metadata_db_user;
