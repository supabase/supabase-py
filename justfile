# commands related to realtime
mod realtime "src/realtime/mod.just"
# commands related to supabase
mod supabase "src/supabase/mod.just"

[doc("Lists all available commands")]
default:
    @just --list
    
[doc("Run all available tests")]
test: realtime::pytest && supabase::pytest

[doc("Run pre-commit on all files")]
pre-commit:
    uv run pre-commit run --all-files

[doc("Run CI tests")]
ci: pre-commit && test
