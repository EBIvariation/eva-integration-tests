// Pre-seed MongoDB for deprecation integration tests.
db = db.getSiblingDB('eva_accession_sharded');

// submittedVariantEntity: 3 variants for project PRJEB12345 / assembly GCA_000004515.4
db.submittedVariantEntity.insertMany([
  {
    _id: 'A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2',
    seq: 'GCA_000004515.4',
    tax: 3847,
    study: 'PRJEB12345',
    contig: 'CM000834.3',
    start: Long('315'),
    ref: 'G', alt: 'C',
    accession: Long('100000001'),
    version: 1,
    createdDate: new Date('2021-04-28T16:32:11.168Z')
  },
  {
    _id: 'B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3',
    seq: 'GCA_000004515.4',
    tax: 3847,
    study: 'PRJEB12345',
    contig: 'CM000834.3',
    start: Long('420'),
    ref: 'A', alt: 'T',
    accession: Long('100000002'),
    version: 1,
    createdDate: new Date('2021-04-28T16:32:11.168Z')
  },
  {
    _id: 'C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4',
    seq: 'GCA_000004515.4',
    tax: 3847,
    study: 'PRJEB12345',
    contig: 'CM000834.3',
    start: Long('530'),
    ref: 'T', alt: 'C',
    accession: Long('100000003'),
    version: 1,
    createdDate: new Date('2021-04-28T16:32:11.168Z')
  }
]);

// Database name 'eva_glycine_max_v2' matches the assembly_code 'glycine_max_v2' stored in
// EVAPRO's assembly_set table for taxonomy 3847 (Glycine max / soybean), as resolved by
// resolve_variant_warehouse_db_name() in ebi_eva_internal_pyutils.
db = db.getSiblingDB('eva_glycine_max_v2');

// variants_2_0 and files_2_0: for drop_study task
db.variants_2_0.insertMany([
  {
    _id: 'CM000834.3_315_G_C',
    chr: 'CM000834.3',
    start: 315,
    _at: { chunkIds: [ 'CM000834.3_0_1k', 'CM000834.3_0_10k' ] },
    alt: 'C',
    end: 315,
    files: [
      {
        fid: 'ERZ99999',
        sid: 'PRJEB12345',
        attrs: { QUAL: '100', AC: '1', AF: '0.5', AN: '2' },
        fm: 'GT',
        samp: { def: '0/1' }
      }
    ],
    hgvs: [ { type: 'genomic', name: 'CM000834.3:g.315G>C' } ],
    len: 1,
    ref: 'G',
    type: 'SNV',
    annot: []
  },
  {
    _id: 'CM000834.3_420_A_T',
    chr: 'CM000834.3',
    start: 420,
    _at: { chunkIds: [ 'CM000834.3_0_1k', 'CM000834.3_0_10k' ] },
    alt: 'T',
    end: 420,
    files: [
      {
        fid: 'ERZ99999',
        sid: 'PRJEB12345',
        attrs: { QUAL: '100', AC: '1', AF: '0.5', AN: '2' },
        fm: 'GT',
        samp: { def: '0/1' }
      }
    ],
    hgvs: [ { type: 'genomic', name: 'CM000834.3:g.420A>T' } ],
    len: 1,
    ref: 'A',
    type: 'SNV',
    annot: []
  }
]);

db.files_2_0.insertMany([
  { sid: 'PRJEB12345', fid: 'ERZ99999', fname: 'test_sample.vcf.gz' }
]);
