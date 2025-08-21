install:
	poetry install

install_poetry:
	curl -sSL https://install.python-poetry.org | python -
	poetry install

tests: install tests_only tests_pre_commit

tests_pre_commit:
	poetry run pre-commit run --all-files

run_infra:
	npx supabase --workdir infra start -x studio,gotrue,postgrest,mailpit,realtime,edge-runtime,logflare,vector,supavisor

stop_infra:
	npx supabase --workdir infra stop

run_tests: tests

local_tests: run_infra sleep tests

tests_only:
	poetry run pytest --cov=./ --cov-report=xml --cov-report=html -vv

build_sync:
	poetry run unasync storage3 tests
	sed -i '0,/SyncMock, /{s/SyncMock, //}' tests/_sync/test_bucket.py tests/_sync/test_client.py
	sed -i 's/SyncMock/Mock/g' tests/_sync/test_bucket.py tests/_sync/test_client.py
	sed -i 's/SyncClient/Client/g' storage3/_sync/client.py storage3/_sync/bucket.py storage3/_sync/file_api.py tests/_sync/test_bucket.py tests/_sync/test_client.py
	sed -i 's/self\.session\.aclose/self\.session\.close/g' storage3/_sync/client.py

sleep:
	sleep 2
