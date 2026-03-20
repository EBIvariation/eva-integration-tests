\c metadata_db

CREATE SCHEMA eva_progress_tracker AUTHORIZATION metadata_db_user;

CREATE TABLE eva_progress_tracker.clustering_release_tracker (
	taxonomy int4 NOT NULL,
	scientific_name text NOT NULL,
	assembly_accession text NOT NULL,
	release_version int8 NOT NULL,
	sources text NOT NULL,
	release_start timestamp NULL,
	release_end timestamp NULL,
	fasta_path text NULL,
	report_path text NULL,
	tempmongo_instance text NULL,
	should_be_released bool NULL,
	num_rs_to_release int8 NULL,
	total_num_variants int8 NULL,
	release_folder_name text NULL,
	release_status text NULL,
	CONSTRAINT clustering_release_tracker_pkey PRIMARY KEY (taxonomy, assembly_accession, release_version)
);

ALTER TABLE eva_progress_tracker.clustering_release_tracker OWNER TO metadata_db_user;
GRANT ALL ON TABLE eva_progress_tracker.clustering_release_tracker TO metadata_db_user;
GRANT ALL ON SCHEMA eva_progress_tracker TO metadata_db_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA eva_progress_tracker TO metadata_db_user;

CREATE SCHEMA eva_stats AUTHORIZATION metadata_db_user;

CREATE TABLE eva_stats.release_rs (
	release_date DATE NOT NULL,
	release_version INT NOT NULL
);

ALTER TABLE eva_stats.release_rs OWNER TO metadata_db_user;
GRANT ALL ON TABLE eva_stats.release_rs TO metadata_db_user;
GRANT ALL ON SCHEMA eva_stats TO metadata_db_user;
