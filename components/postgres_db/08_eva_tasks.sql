-- Connect to the database
\c metadata_db

--- schema (eva_tasks)
CREATE SCHEMA eva_tasks AUTHORIZATION metadata_db_user;

--- table (contig analysis - ONLY USED for custom assembly script)
CREATE TABLE eva_tasks.eva2469_contig_analysis (
	assembly_accession text NULL,
	contig_accession text NULL,
	source_table text NULL,
	refseq_assembly_from_equiv_table text NULL,
	gebank_assembly_from_equiv_table text NULL,
	refseq_contig_from_equiv_table text NULL,
	genbank_contig_from_equiv_table text NULL,
	genbank_assembly_from_asm_rpt text NULL,
	contig_name_from_asm_rpt text NULL,
	refseq_contig_from_asm_rpt text NULL,
	genbank_contig_from_asm_rpt text NULL,
	is_equiv_genbank_available_in_asm_rpt bool NULL,
	is_contig_in_asm_rpt bool NULL
);

ALTER TABLE eva_tasks.eva2469_contig_analysis OWNER to metadata_db_user;
GRANT ALL ON TABLE eva_tasks.eva2469_contig_analysis to metadata_db_user;
