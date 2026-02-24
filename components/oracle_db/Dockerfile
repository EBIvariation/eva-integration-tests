FROM gvenzl/oracle-free:slim

COPY 01_era_data.sql /container-entrypoint-initdb.d/
COPY 02_era_ingestion_data.sql /container-entrypoint-initdb.d/

# should be the last file to be copied and executed
COPY 99_init_complete.sql /container-entrypoint-initdb.d/