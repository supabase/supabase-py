-- examples/fastapi/supabase/migrations/001_initial.sql

-- tasks: the event source for Postgres Changes
CREATE TABLE tasks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'in_progress', 'done')),
    assigned_to UUID REFERENCES auth.users (id),
    created_by  UUID REFERENCES auth.users (id) DEFAULT auth.uid(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- rules: user-defined watch conditions
CREATE TABLE rules (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES auth.users (id) DEFAULT auth.uid(),
    watch_column      TEXT NOT NULL,
    watch_value       TEXT NOT NULL,
    broadcast_channel TEXT NOT NULL,
    label             TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- rule_events: append-only log written by the service role engine
CREATE TABLE rule_events (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id      UUID NOT NULL REFERENCES rules (id) ON DELETE CASCADE,
    task_id      UUID NOT NULL REFERENCES tasks (id) ON DELETE CASCADE,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload      JSONB
);

-- RLS
ALTER TABLE tasks       ENABLE ROW LEVEL SECURITY;
ALTER TABLE rules       ENABLE ROW LEVEL SECURITY;
ALTER TABLE rule_events ENABLE ROW LEVEL SECURITY;

-- tasks: all authenticated users can read and create; only update their own
CREATE POLICY "tasks_select" ON tasks
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "tasks_insert" ON tasks
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "tasks_update" ON tasks
    FOR UPDATE TO authenticated
    USING (assigned_to = auth.uid())
    WITH CHECK (assigned_to = auth.uid());

-- rules: users own their rules
CREATE POLICY "rules_select" ON rules
    FOR SELECT TO authenticated USING (user_id = auth.uid());

CREATE POLICY "rules_insert" ON rules
    FOR INSERT TO authenticated WITH CHECK (user_id = auth.uid());

CREATE POLICY "rules_delete" ON rules
    FOR DELETE TO authenticated USING (user_id = auth.uid());

-- rule_events: users can read events belonging to their rules
CREATE POLICY "rule_events_select" ON rule_events
    FOR SELECT TO authenticated
    USING (
        rule_id IN (SELECT id FROM rules WHERE user_id = auth.uid())
    );

-- Enable Realtime for tasks so the Python engine receives Postgres Changes
ALTER PUBLICATION supabase_realtime ADD TABLE tasks;

-- Grant table-level privileges so PostgREST can execute queries.
-- Supabase's default privileges are set for supabase_admin; migrations run as
-- postgres so tables need explicit grants.  RLS policies still control row access.
GRANT SELECT, INSERT, UPDATE ON TABLE tasks       TO authenticated;
GRANT SELECT, INSERT, DELETE ON TABLE rules       TO authenticated;
GRANT SELECT               ON TABLE rule_events   TO authenticated;

-- service_role bypasses RLS and is used by the realtime engine.
GRANT ALL ON TABLE tasks, rules, rule_events      TO service_role;
