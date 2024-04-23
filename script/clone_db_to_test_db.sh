ROOT_USER="postgresql://postgres:password@localhost:8888/"


psql $ROOT_USER -c "DROP DATABASE IF EXISTS test_db;"
psql $ROOT_USER -c "DROP ROLE IF EXISTS test_user;"
psql $ROOT_USER -c "CREATE ROLE test_user WITH LOGIN PASSWORD 'password';"
psql $ROOT_USER -c "CREATE DATABASE test_db OWNER test_user;"
export TEST_DB="postgresql://test_user:password@localhost:8888/test_db"
psql $TEST_DB -c "CREATE SCHEMA IF NOT EXISTS memgpt;"
psql "postgresql://postgres:password@localhost:8888/test_db" -c "CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA memgpt;"

pg_dump $POSTGRES_URL --format=custom > db.dump

pg_restore -U postgres -d test_db -h localhost -p 8888 --no-owner --role=test_user< db.dump

psql $TEST_DB -c "ALTER DATABASE test_db SET SEARCH_PATH TO memgpt;"

rm db.dump

export POSTGRES_URL=$TEST_DB
export DATABASE_URL=$TEST_DB