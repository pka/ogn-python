#!/usr/bin/env bash
# wait a bit for db and backend to properly start
echo Waiting backend to start...
#bash -c 'while !</dev/tcp/$BACKENDHOST/$BACKENDPORT; do sleep 1; done;' 2> /dev/null
bash -c 'until /usr/lib/postgresql/13/bin/pg_isready; do sleep 1; done'
psql -t -d ogn -c "SELECT EXISTS ( SELECT 1 FROM information_schema.tables WHERE table_name = 'elevation' )" | grep -q t
if [ $? -eq 1 ]
then
    echo Importing elevation...
    raster2pgsql /data/*.tif -s 4326 -d -M -C -I -F -t 25x25 public.elevation | psql -q -d ogn
    echo Importing borders...
    cat /extra/world_borders_temp | psql -d ogn > /dev/null
    psql -d ogn -c "INSERT INTO countries SELECT * FROM world_borders_temp;"
    psql -d ogn -c "DROP TABLE world_borders_temp;"
fi
echo Elevation and borders added
while true; do sleep 10000; done;
