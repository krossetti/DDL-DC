
-- replace OWNER name below with yours
CREATE DATABASE whitehouse
  WITH OWNER = "postgres"
       ENCODING = 'UTF8'
       TABLESPACE = pg_default
       LC_COLLATE = 'en_US.UTF-8'
       LC_CTYPE = 'en_US.UTF-8'
       CONNECTION LIMIT = -1;

CREATE TABLE visitors
(
  last_name character varying,
  first_name character varying,
  name_id character varying,
  uin character varying,
  building_nr character varying,
  access_type character varying,
  toa character varying,
  poa character varying,
  tod character varying,
  pod character varying,
  appt_made character varying,
  appt_start character varying,
  appt_end character varying,
  appt_cancel character varying,
  total_people character varying,
  last_update character varying,
  post character varying,
  last_entry character varying,
  terminal_suffix character varying,
  visitee_namelast character varying,
  visitee_namefirst character varying,
  meeting_loc character varying,
  meeting_room character varying,
  caller_namelast character varying,
  caller_namefirst character varying,
  caller_room character varying,
  description character varying,
  release_date character varying
)
WITH (
  OIDS=FALSE
);

-- replace OWNER name below with yours
ALTER TABLE visitors
  OWNER TO "postgres";

-- replace filepath below with your path to the dataset
COPY visitors FROM '/Users/Tinkerbell/Desktop/DDL/visitors/fixtures/whitehouse-visitors.csv' DELIMITER ',' CSV HEADER;
