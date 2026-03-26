FROM postgres:11

COPY 01_contig_alias.sql /docker-entrypoint-initdb.d/
COPY 02_eva_pro.sql /docker-entrypoint-initdb.d/
COPY 03_eva_submissions.sql /docker-entrypoint-initdb.d/
COPY 04_eva_pro_inserts_for_ingestion.sql /docker-entrypoint-initdb.d/
COPY 05_variant_jt.sql /docker-entrypoint-initdb.d/
COPY 06_accession_jt.sql /docker-entrypoint-initdb.d/
COPY 07_eva_progress_tracker.sql /docker-entrypoint-initdb.d/
COPY 08_eva_tasks.sql /docker-entrypoint-initdb.d/