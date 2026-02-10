FROM gvenzl/oracle-free:slim

COPY 01-era-data.sql /container-entrypoint-initdb.d/
COPY 02-era-ingestion-data.sql /container-entrypoint-initdb.d/

# should be the last file to be copied and executed
COPY 100-init-complete.sql /container-entrypoint-initdb.d/