-- Connect to the database
\c metadata_db

-- Inserts for eva_submission_status_cv
INSERT INTO evapro.eva_submission_status_cv (eva_submission_status_id, submission_status, description)
VALUES (-1,'Submission Private','The submission is private at EVA (e.g. hide parent project)'),
        (0,'Submission Defined','A submission has been initiated, but not files yet received'),
       (1,'Files Received','EVA has receieved the submission files'),
       (2,'VCF File Valid','The VCF files are technically valid'),
       (3,'Meta-data Valid','The required meta-data is complete and correct'),
       (4,'ENA Project Accession Assigned','A project accession has be assigned by ENA'),
       (5,'File submitted to ENA','The VCF files have been submitted to ENA'),
       (6,'ENA Submission Complete','The ENA submission is complete'),
       (7,'EVA Processing Started','The files have started to be processed by EVA'),
       (8,'EVA Processing Complete','The files have completed processing by EVA'),
       (9,'Mongo Loading Started','The data is loading to MongoDB'),
       (10,'Submission Live','The submission is live and public at EVA');


--- Inserts for file_class_cv
INSERT INTO evapro.file_class_cv (file_class_id, file_class)
VALUES (1, 'submitted');
INSERT INTO evapro.file_class_cv (file_class_id, file_class)
VALUES (2, 'eva_brokered');
INSERT INTO evapro.file_class_cv (file_class_id, file_class)
VALUES (3, 'eva_value_added');
INSERT INTO evapro.file_class_cv (file_class_id, file_class)
VALUES (4, 'fixed_for_eva');

--- Inserts for taxonomy
INSERT INTO evapro.taxonomy (taxonomy_id, common_name, scientific_name, taxonomy_code, eva_name)
VALUES (4896, 'fission yeast', 'Schizosaccharomyces pombe', 'spombe', 'fission yeast');

--- Inserts for assembly_set
INSERT INTO evapro.assembly_set (assembly_set_id, taxonomy_id, assembly_name, assembly_code)
VALUES (34, 4896, 'ASM294v2', 'asm294v2');

--- Inserts for accessioned_assembly
INSERT INTO evapro.accessioned_assembly (assembly_set_id, assembly_accession, assembly_chain, assembly_version)
VALUES (34, 'GCA_000002945.2', 'GCA_000002945', 2);