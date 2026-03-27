\c metadata_db

CREATE SCHEMA eva_stats AUTHORIZATION metadata_db_user;

CREATE TABLE eva_stats.release_rs (
	release_date DATE NOT NULL,
	release_version INT NOT NULL
);

ALTER TABLE eva_stats.release_rs OWNER TO metadata_db_user;
GRANT ALL ON TABLE eva_stats.release_rs TO metadata_db_user;
