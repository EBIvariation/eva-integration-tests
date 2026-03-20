-- Connect to the database
\c metadata_db

--- schema (eva_progress_tracker)
CREATE SCHEMA eva_progress_tracker AUTHORIZATION metadata_db_user;

--- table (remapping_tracker)
CREATE TABLE eva_progress_tracker.remapping_tracker (
	"source" text NOT NULL,
	taxonomy int4 NOT NULL,
	scientific_name text NULL,
	origin_assembly_accession text NOT NULL,
	num_studies int4 NOT NULL,
	num_ss_ids int8 NOT NULL,
	release_version int4 NOT NULL,
	assembly_accession text NULL,
	remapping_report_time timestamp DEFAULT now() NULL,
	remapping_status text NULL,
	remapping_start timestamp NULL,
	remapping_end timestamp NULL,
	remapping_version text NULL,
	num_ss_extracted int4 NULL,
	num_ss_remapped int4 NULL,
	num_ss_ingested int4 NULL,
	study_accessions _text NULL,
	CONSTRAINT remapping_tracker_pkey PRIMARY KEY (source, taxonomy, origin_assembly_accession, release_version)
);

ALTER TABLE eva_progress_tracker.remapping_tracker OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_progress_tracker.remapping_tracker to metadata_db_user;


--- table (clustering_release_tracker)
CREATE TABLE eva_progress_tracker.clustering_release_tracker (
	taxonomy int4 NOT NULL,
	scientific_name text NOT NULL,
	assembly_accession text NOT NULL,
	release_version int8 NOT NULL,
	sources text NOT NULL,
	clustering_status text NULL,
	clustering_start timestamp NULL,
	clustering_end timestamp NULL,
	should_be_clustered bool NULL,
	fasta_path text NULL,
	report_path text NULL,
	tempmongo_instance text NULL,
	should_be_released bool NULL,
	num_rs_to_release int8 NULL,
	total_num_variants int8 NULL,
	release_folder_name text NULL,
	release_status text NULL,
	release_start timestamp NULL,
	release_end timestamp NULL,
	CONSTRAINT clustering_release_tracker_pkey PRIMARY KEY (taxonomy, assembly_accession, release_version)
);

ALTER TABLE eva_progress_tracker.clustering_release_tracker OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_progress_tracker.clustering_release_tracker to metadata_db_user;
