CREATE USER accession_jt_user WITH PASSWORD 'accession_jt_pass';
CREATE DATABASE accession_jt;
-- Connect to the database
\c accession_jt

CREATE TABLE public.batch_job_instance (
	job_instance_id int8 NOT NULL,
	"version" int8 NULL,
	job_name varchar(100) NOT NULL,
	job_key varchar(32) NOT NULL,
	CONSTRAINT batch_job_instance_pkey PRIMARY KEY (job_instance_id),
	CONSTRAINT job_inst_un UNIQUE (job_name, job_key)
);

CREATE TABLE public.batch_job_execution (
	job_execution_id int8 NOT NULL,
	"version" int8 NULL,
	job_instance_id int8 NOT NULL,
	create_time timestamp NOT NULL,
	start_time timestamp NULL,
	end_time timestamp NULL,
	status varchar(10) NULL,
	exit_code varchar(2500) NULL,
	exit_message varchar(2500) NULL,
	last_updated timestamp NULL,
	job_configuration_location varchar(2500) NULL,
	CONSTRAINT batch_job_execution_pkey PRIMARY KEY (job_execution_id),
	CONSTRAINT job_inst_exec_fk FOREIGN KEY (job_instance_id) REFERENCES public.batch_job_instance(job_instance_id)
);

CREATE TABLE public.batch_job_execution_params (
	job_execution_id int8 NOT NULL,
	type_cd varchar(6) NOT NULL,
	key_name varchar(100) NOT NULL,
	string_val varchar(500) NULL,
	date_val timestamp NULL,
	long_val int8 NULL,
	double_val float8 NULL,
	identifying bpchar(1) NOT NULL,
	CONSTRAINT job_exec_params_fk FOREIGN KEY (job_execution_id) REFERENCES public.batch_job_execution(job_execution_id)
);

CREATE TABLE public.batch_step_execution (
	step_execution_id int8 NOT NULL,
	"version" int8 NOT NULL,
	step_name varchar(100) NOT NULL,
	job_execution_id int8 NOT NULL,
	start_time timestamp NOT NULL,
	end_time timestamp NULL,
	status varchar(10) NULL,
	commit_count int8 NULL,
	read_count int8 NULL,
	filter_count int8 NULL,
	write_count int8 NULL,
	read_skip_count int8 NULL,
	write_skip_count int8 NULL,
	process_skip_count int8 NULL,
	rollback_count int8 NULL,
	exit_code varchar(2500) NULL,
	exit_message varchar(2500) NULL,
	last_updated timestamp NULL,
	CONSTRAINT batch_step_execution_pkey PRIMARY KEY (step_execution_id),
	CONSTRAINT job_exec_step_fk FOREIGN KEY (job_execution_id) REFERENCES public.batch_job_execution(job_execution_id)
);

CREATE TABLE public.batch_step_execution_context (
	step_execution_id int8 NOT NULL,
	short_context varchar(2500) NOT NULL,
	serialized_context text NULL,
	CONSTRAINT batch_step_execution_context_pkey PRIMARY KEY (step_execution_id),
	CONSTRAINT step_exec_ctx_fk FOREIGN KEY (step_execution_id) REFERENCES public.batch_step_execution(step_execution_id)
);

CREATE TABLE public.batch_job_execution_context (
	job_execution_id int8 NOT NULL,
	short_context varchar(2500) NOT NULL,
	serialized_context text NULL,
	CONSTRAINT batch_job_execution_context_pkey PRIMARY KEY (job_execution_id),
	CONSTRAINT job_exec_ctx_fk FOREIGN KEY (job_execution_id) REFERENCES public.batch_job_execution(job_execution_id)
);

CREATE TABLE public.contiguous_id_blocks (
	id int8 NOT NULL,
	application_instance_id varchar(255) NOT NULL,
	category_id varchar(255) NOT NULL,
	"first_value" int8 NOT NULL,
	last_committed int8 NOT NULL,
	"last_value" int8 NOT NULL,
	reserved bool NOT NULL,
	last_updated_timestamp timestamp NOT NULL,
	CONSTRAINT allotted_block_range CHECK (((((last_value - first_value) + 1))::numeric = '100000'::numeric)),
	CONSTRAINT first_value_range CHECK ((((first_value)::numeric >= '3000000000'::numeric) AND ((floor((((first_value)::numeric - '3000000000'::numeric) / '1000000000'::numeric)) % (2)::numeric) = (0)::numeric))),
	CONSTRAINT last_value_range CHECK ((((last_value)::numeric >= (('3000000000'::numeric + '100000'::numeric) - (1)::numeric)) AND ((floor((((last_value)::numeric - '3000000000'::numeric) / '1000000000'::numeric)) % (2)::numeric) = (0)::numeric))),
	CONSTRAINT uk6o6je7va9q8oimxa6hp37cwce UNIQUE (category_id, first_value),
	CONSTRAINT uniq_category_first_value UNIQUE (category_id, first_value)
);

CREATE SEQUENCE public.batch_step_execution_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

CREATE SEQUENCE public.batch_job_execution_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

CREATE SEQUENCE public.batch_job_seq
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

CREATE SEQUENCE public.hibernate_sequence
	INCREMENT BY 1
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

--- Permissions


ALTER TABLE public.batch_job_instance OWNER TO accession_jt_user;
GRANT ALL ON TABLE public.batch_job_instance TO accession_jt_user;

ALTER TABLE public.batch_job_execution OWNER TO accession_jt_user;
GRANT ALL ON TABLE public.batch_job_execution TO accession_jt_user;

ALTER TABLE public.batch_job_execution_params OWNER TO accession_jt_user;
GRANT ALL ON TABLE public.batch_job_execution_params TO accession_jt_user;

ALTER TABLE public.batch_step_execution OWNER TO accession_jt_user;
GRANT ALL ON TABLE public.batch_step_execution TO accession_jt_user;

ALTER TABLE public.batch_step_execution_context OWNER TO accession_jt_user;
GRANT ALL ON TABLE public.batch_step_execution_context TO accession_jt_user;

ALTER TABLE public.batch_job_execution_context OWNER TO accession_jt_user;
GRANT ALL ON TABLE public.batch_job_execution_context TO accession_jt_user;

ALTER TABLE public.contiguous_id_blocks OWNER TO accession_jt_user;
GRANT ALL ON TABLE public.contiguous_id_blocks TO accession_jt_user;

ALTER SEQUENCE public.batch_step_execution_seq OWNER TO accession_jt_user;
GRANT ALL ON SEQUENCE public.batch_step_execution_seq TO accession_jt_user;

ALTER SEQUENCE public.batch_job_execution_seq OWNER TO accession_jt_user;
GRANT ALL ON SEQUENCE public.batch_job_execution_seq TO accession_jt_user;

ALTER SEQUENCE public.batch_job_seq OWNER TO accession_jt_user;
GRANT ALL ON SEQUENCE public.batch_job_seq TO accession_jt_user;

ALTER SEQUENCE public.hibernate_sequence OWNER TO accession_jt_user;
GRANT ALL ON SEQUENCE public.hibernate_sequence TO accession_jt_user;