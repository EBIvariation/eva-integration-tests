FROM postgres:11

COPY 01_contig_alias.sql /docker-entrypoint-initdb.d/
COPY 02_eva_pro.sql /docker-entrypoint-initdb.d/
COPY 03_eva_submissions.sql /docker-entrypoint-initdb.d/