# commands related to realtime
[group("package")]
[doc("realtime commands")]
mod realtime "src/realtime/mod.just"
[doc("supabase commands")]
[group("package")]
mod supabase "src/supabase/mod.just"

[doc("Lists all available commands")]
default:
    @just --list

[doc("Run all available tests")]
test: realtime::test supabase::test

[doc("Run pre-commit on all files")]
pre-commit:
    uv run pre-commit run --all-files

[doc("Run CI tests")]
ci: pre-commit test
