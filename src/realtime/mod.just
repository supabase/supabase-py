[doc("Lists all available commands")]
default:
    @just --list realtime


[doc("Run pytest in realtime")]
pytest: infra
    uv run --exact --package realtime pytest  --cov=./ --cov-report=xml --cov-report=html

[doc("Start the supabase docker instance for realtime")]
infra:
    supabase start --workdir infra -x studio,mailpit,edge-runtime,logflare,vector,supavisor,imgproxy,storage-api
