-- The typed builder's aggregates, sum() to count(), need PostgREST's
-- db-aggregates-enabled setting, which is off by default.
alter role authenticator set pgrst.db_aggregates_enabled = 'true';
