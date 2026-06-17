CREATE USER contiguous_id_blocks_user WITH PASSWORD 'contiguous_id_blocks_pass';
CREATE DATABASE contiguous_id_blocks_db;
-- Connect to the database
\c contiguous_id_blocks_db

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

CREATE SEQUENCE public.contiguous_id_blocks_seq
	INCREMENT BY 50
	MINVALUE 1
	MAXVALUE 9223372036854775807
	START 1
	CACHE 1
	NO CYCLE;

--- Permissions

ALTER TABLE public.contiguous_id_blocks OWNER TO contiguous_id_blocks_user;
GRANT ALL ON TABLE public.contiguous_id_blocks TO contiguous_id_blocks_user;

ALTER SEQUENCE public.contiguous_id_blocks_seq OWNER TO contiguous_id_blocks_user;
GRANT USAGE, SELECT ON SEQUENCE public.contiguous_id_blocks_seq TO contiguous_id_blocks_user;