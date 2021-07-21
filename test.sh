#!/bin/sh
SUPABASE_TEST_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlhdCI6MTYxMjYwOTMyMiwiZXhwIjoxOTI4MTg1MzIyfQ.XL9W5I_VRQ4iyQHVQmjG0BkwRfx6eVyYB3uAKcesukg" \
SUPABASE_TEST_URL="https://tfsatoopsijgjhrqplra.supabase.co" \
poetry run pytest
