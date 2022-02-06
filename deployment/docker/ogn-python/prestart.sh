#!/usr/bin/env bash
echo Waiting db to start...
#bash -c 'while !</dev/tcp/$PGHOST/5432; do sleep 1; done;' 2> /dev/null
bash -c 'until /usr/lib/postgresql/13/bin/pg_isready; do sleep 1; done'
flask database init
#flask database init_timescaledb
find /cups -name "*.cup" -exec flask database import_airports  {} \;
#flask database import_ddb
