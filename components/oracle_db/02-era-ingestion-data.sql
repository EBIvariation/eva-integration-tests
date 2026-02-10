CONNECT sys/oracle_pass@//localhost:1521/FREEPDB1 as sysdba

INSERT INTO era.PROJECT (PROJECT_ID, CENTER_NAME, PROJECT_ALIAS, FIRST_CREATED, PROJECT_TITLE, TAX_ID, SCIENTIFIC_NAME,
                         COMMON_NAME, PROJECT_XML)
VALUES ('PRJEB105137', 'King Abdullah University of Science and Technology',
        'ELOAD_1513', TIMESTAMP '2025-12-09 21:50:31', 'Natural variants for the 20K Rice Genome Project',
        4530, 'Oryza sativa', NULL,
        '<?xml version="1.0" encoding="UTF-8"?>
    <PROJECT_SET>
      <PROJECT alias="ELOAD_1513" center_name="King Abdullah University of Science and Technology" broker_name="EBI" accession="PRJEB105137">
        <IDENTIFIERS>
          <PRIMARY_ID>PRJEB105137</PRIMARY_ID>
          <SUBMITTER_ID namespace="King Abdullah University of Science and Technology">ELOAD_1513</SUBMITTER_ID>
        </IDENTIFIERS>
        <TITLE>Natural variants for the 20K Rice Genome Project</TITLE>
        <DESCRIPTION>An Investigation of rice genetic variation using the 20K Rice Genome Project</DESCRIPTION>
        <SUBMISSION_PROJECT>
          <SEQUENCING_PROJECT/>
          <ORGANISM>
            <TAXON_ID>4530</TAXON_ID>
            <SCIENTIFIC_NAME>Oryza sativa</SCIENTIFIC_NAME>
          </ORGANISM>
        </SUBMISSION_PROJECT>
      </PROJECT>
    </PROJECT_SET>');


INSERT INTO era.STUDY (STUDY_ID, PROJECT_ID, SUBMISSION_ID, STUDY_TYPE, STUDY_XML)
VALUES ('ERP186339', 'PRJEB105137', 'ERA35393650', 'Other',
        '<?xml version="1.0" encoding="UTF-8"?>
    <STUDY_SET>
      <STUDY alias="ELOAD_1513" center_name="King Abdullah University of Science and Technology" broker_name="EBI" accession="ERP186339">
        <IDENTIFIERS>
          <PRIMARY_ID>ERP186339</PRIMARY_ID>
          <SUBMITTER_ID namespace="King Abdullah University of Science and Technology">ELOAD_1513</SUBMITTER_ID>
        </IDENTIFIERS>
        <DESCRIPTOR>
          <STUDY_TITLE>Natural variants for the 20K Rice Genome Project</STUDY_TITLE>
          <STUDY_TYPE existing_study_type="Other"/>
          <STUDY_ABSTRACT>An Investigation of rice genetic variation using the 20K Rice Genome Project</STUDY_ABSTRACT>
        </DESCRIPTOR>
      </STUDY>
    </STUDY_SET>');



INSERT INTO era.SUBMISSION (SUBMISSION_ID, SUBMISSION_XML, LAST_UPDATED)
VALUES ('ERA35393650',
        '<?xml version="1.0" encoding="UTF-8"?>
<SUBMISSION_SET>
  <SUBMISSION alias="ELOAD_1513" center_name="King Abdullah University of Science and Technology" broker_name="EBI" submission_date="2025-12-09T21:49:58.858Z" accession="ERA35393650">
    <IDENTIFIERS>
      <PRIMARY_ID>ERA35393650</PRIMARY_ID>
      <SUBMITTER_ID namespace="King Abdullah University of Science and Technology">ELOAD_1513</SUBMITTER_ID>
    </IDENTIFIERS>
    <ACTIONS>
      <ACTION>
        <ADD/>
      </ACTION>
      <ACTION>
        <HOLD HoldUntilDate="2027-03-12"/>
      </ACTION>
    </ACTIONS>
  </SUBMISSION>
</SUBMISSION_SET>'
           ,
        TIMESTAMP '2025-12-09 21:50:31');

INSERT INTO ERA.ANALYSIS (ANALYSIS_ID, SUBMISSION_ID, ANALYSIS_TITLE, ANALYSIS_ALIAS, ANALYSIS_TYPE, CENTER_NAME,
                          FIRST_CREATED, ANALYSIS_XML, STATUS_ID, SUBMISSION_ACCOUNT_ID, STUDY_ID, BIOPROJECT_ID)
VALUES ('ERZ28769990',
        'ERA35393650',
        'Rice genetic variation analysis for InDels',
        'ELOAD_1513_RDGB InDel analysis',
        'SEQUENCE_VARIATION',
        'Wing Lab KAUST',
        TIMESTAMP '2025-12-09 21:51:41',
        '<?xml version="1.0" encoding="UTF-8"?>
    <ANALYSIS_SET>
        <ANALYSIS alias="ELOAD_1513_RDGB InDel analysis" center_name="Wing Lab KAUST" broker_name="EBI" accession="ERZ28769990">
            <IDENTIFIERS>
                <PRIMARY_ID>ERZ28769990</PRIMARY_ID>
                <SUBMITTER_ID namespace="Wing Lab KAUST">ELOAD_1513_RDGB InDel analysis</SUBMITTER_ID>
            </IDENTIFIERS>
            <TITLE>Rice genetic variation analysis for InDels</TITLE>
            <DESCRIPTION>InDels for 20K-RGP using IRGSP as a reference</DESCRIPTION>
            <STUDY_REF accession="ERP186339">
                <IDENTIFIERS>
                    <PRIMARY_ID>ERP186339</PRIMARY_ID>
                    <SECONDARY_ID>PRJEB105137</SECONDARY_ID>
                </IDENTIFIERS>
            </STUDY_REF>
            <ANALYSIS_TYPE>
                <SEQUENCE_VARIATION>
                    <ASSEMBLY>
                        <STANDARD accession="GCA_001433935.1"/>
                    </ASSEMBLY>
                    <EXPERIMENT_TYPE>Whole genome sequencing</EXPERIMENT_TYPE>
                    <PROGRAM>HPC-GVCW (GATK4)</PROGRAM>
                    <PLATFORM>Illumina HiSeq 4000</PLATFORM>
                </SEQUENCE_VARIATION>
            </ANALYSIS_TYPE>
            <FILES>
                <FILE checksum="77b3f2576319887b36479474c39bf5e6" checksum_method="MD5" filename="analysis/ERZ287/ERZ28769990/genome1.genomewide.INDELs.withID.PlinkFormat.sort.vcf.gz" filetype="vcf"/>
                <FILE checksum="bbca217c4ca11a8068b11fb9fb051a5e" checksum_method="MD5" filename="analysis/ERZ287/ERZ28769990/genome1.genomewide.INDELs.withID.PlinkFormat.sort.vcf.csi" filetype="csi"/>
            </FILES>
            <ANALYSIS_ATTRIBUTES>
                <ANALYSIS_ATTRIBUTE>
                    <TAG>Pipeline_Description</TAG>
                    <VALUE>HPC-GVCW based on GATK4 to identify rice variants.</VALUE>
                </ANALYSIS_ATTRIBUTE>
            </ANALYSIS_ATTRIBUTES>
        </ANALYSIS>
    </ANALYSIS_SET>',
        2,
        'Webin-1008',
        'ERP186339',
        'PRJEB105137');

INSERT INTO ERA.WEBIN_FILE (SUBMISSION_FILE_ID, DATA_FILE_OWNER_ID, DATA_FILE_PATH, CHECKSUM, DATA_FILE_FORMAT, BYTES)
VALUES ('ERF219841043', 'ERZ28769990',
        'analysis/ERZ287/ERZ28769990/genome1.genomewide.INDELs.withID.PlinkFormat.sort.vcf.gz',
        '77b3f2576319887b36479474c39bf5e6', 'VCF', 50824503470);
INSERT INTO ERA.WEBIN_FILE (SUBMISSION_FILE_ID, DATA_FILE_OWNER_ID, DATA_FILE_PATH, CHECKSUM, DATA_FILE_FORMAT, BYTES)
VALUES ('ERF219841044', 'ERZ28769990',
        'analysis/ERZ287/ERZ28769990/genome1.genomewide.INDELs.withID.PlinkFormat.sort.vcf.csi',
        'bbca217c4ca11a8068b11fb9fb051a5e', 'CSI', 335146);

INSERT INTO ERA.ANALYSIS_SUBMISSION_FILE (ANALYSIS_ID)
VALUES ('ERZ28769990');

INSERT INTO ERA.ANALYSIS_SAMPLE (ANALYSIS_ID, SAMPLE_ID) VALUES ('ERZ28769990', 'DRS029882');
INSERT INTO ERA.ANALYSIS_SAMPLE (ANALYSIS_ID, SAMPLE_ID) VALUES ('ERZ28769990', 'DRS029883');
INSERT INTO ERA.ANALYSIS_SAMPLE (ANALYSIS_ID, SAMPLE_ID) VALUES ('ERZ28769990', 'DRS029884');
INSERT INTO ERA.ANALYSIS_SAMPLE (ANALYSIS_ID, SAMPLE_ID) VALUES ('ERZ28769990', 'DRS029885');
INSERT INTO ERA.ANALYSIS_SAMPLE (ANALYSIS_ID, SAMPLE_ID) VALUES ('ERZ28769990', 'DRS029886');

INSERT INTO ERA.SAMPLE (SAMPLE_ID, BIOSAMPLE_ID) VALUES ('DRS029882', 'SAMD00045866');
INSERT INTO ERA.SAMPLE (SAMPLE_ID, BIOSAMPLE_ID) VALUES ('DRS029883', 'SAMD00045867');
INSERT INTO ERA.SAMPLE (SAMPLE_ID, BIOSAMPLE_ID) VALUES ('DRS029884', 'SAMD00045868');
INSERT INTO ERA.SAMPLE (SAMPLE_ID, BIOSAMPLE_ID) VALUES ('DRS029885', 'SAMD00045869');
INSERT INTO ERA.SAMPLE (SAMPLE_ID, BIOSAMPLE_ID) VALUES ('DRS029886', 'SAMD00045870');

commit;