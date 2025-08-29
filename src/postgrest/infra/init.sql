CREATE TABLE public.countries (
    id int8 PRIMARY KEY,
    iso CHAR (2) NOT NULL,
    country_name VARCHAR (80) NOT NULL,
    nicename VARCHAR (80) NOT NULL,
    iso3 CHAR (3) DEFAULT NULL,
    numcode SMALLINT DEFAULT NULL,
    phonecode INT NOT NULL
);

INSERT INTO public.countries (id, iso, country_name, nicename, iso3, numcode, phonecode) VALUES
    (1, 'AF', 'AFGHANISTAN', 'Afghanistan', 'AFG', 4, 93),
    (2, 'AL', 'ALBANIA', 'Albania', 'ALB', 8, 355),
    (3, 'DZ', 'ALGERIA', 'Algeria', 'DZA', 12, 213),
    (4, 'AQ', 'ANTARCTICA', 'Antarctica', NULL, NULL, 0),
    (5, 'CR', 'COSTA RICA', 'Costa Rica', 'CRI', 188, 506),
    (6, 'ES', 'SPAIN', 'Spain', 'ESP', 724, 34),
    (7, 'TH', 'THAILAND', 'Thailand', 'THA', 764, 66),
    (8, 'TG', 'TOGO', 'Togo', 'TGO', 768, 228),
    (9, 'TT', 'TRINIDAD AND TOBAGO', 'Trinidad and Tobago', 'TTO', 780, 1868),
    (10, 'GB', 'UNITED KINGDOM', 'United Kingdom', 'GBR', 826, 44),
    (11, 'US', 'UNITED STATES', 'United States', 'USA', 840, 1),
    (12, 'ZW', 'ZIMBABWE', 'Zimbabwe', 'ZWE', 716, 263);

create table public.cities (
    id int8 primary key,
    country_id int8 not null references public.countries,
    name text
);

insert into public.cities (id, name, country_id) values
    (1, 'London', 10),
    (2, 'Manchester', 10),
    (3, 'Liverpool', 10),
    (4, 'Bristol', 10),
    (5, 'Miami', 11),
    (6, 'Huston', 11),
    (7, 'Atlanta', 11);

create table public.users (
    id int8 primary key,
    name text,
    address jsonb
);

insert into public.users (id, name, address) values
    (1, 'Michael', '{ "postcode": 90210, "street": "Melrose Place" }'),
    (2, 'Jane', '{}');

create table public.reservations (
    id int8 primary key,
    room_name text,
    during tsrange
);

insert into public.reservations (id, room_name, during) values
    (1, 'Emerald', '[2000-01-01 13:00, 2000-01-01 15:00)'),
    (2, 'Topaz', '[2000-01-02 09:00, 2000-01-02 10:00)');


create table public.issues (
    id int8 primary key,
    title text,
    tags text[]
);

insert into public.issues (id, title, tags) values
    (1, 'Cache invalidation is not working', array['is:open', 'severity:high', 'priority:low']),
    (2, 'Use better names', array['is:open', 'severity:low', 'priority:medium']),
    (3, 'Add missing postgrest filters', array['is:open', 'severity:low', 'priority:high']),
    (4, 'Add alias to filters', array['is:closed', 'severity:low', 'priority:medium']);

create or replace function public.list_stored_countries()
    returns setof countries
    language sql
as $function$
    select * from countries;
$function$;

create or replace function public.search_countries_by_name(search_name text)
    returns setof countries
    language sql
as $function$
    select * from countries where nicename ilike '%' || search_name || '%';
$function$;

create table
  orchestral_sections (id int8 primary key, name text);
create table
  instruments (
    id int8 primary key,
    section_id int8 not null references orchestral_sections,
    name text
  );

insert into
  orchestral_sections (id, name)
values
  (1, 'strings'),
  (2, 'woodwinds');
insert into
  instruments (id, section_id, name)
values
  (1, 1, 'harp'),
  (2, 1, 'violin');
