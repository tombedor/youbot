ROOT_USER="postgresql://postgres:password@localhost:8888/"


psql $ROOT_USER -c "DROP DATABASE IF EXISTS test_db;"
psql $ROOT_USER -c "DROP DATABASE IF EXISTS memgpt;"
psql $ROOT_USER -c "DROP ROLE IF EXISTS test_user;"
psql $ROOT_USER -c "CREATE ROLE test_user WITH LOGIN PASSWORD 'password';"
psql $ROOT_USER -c "CREATE DATABASE memgpt OWNER test_user;"
export TEST_DB="postgresql://test_user:password@localhost:8888/memgpt"
psql "postgresql://postgres:password@localhost:8888/memgpt" -c "CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;"

pg_dump $REMOTE_URL --format=custom > db.dump

echo "copying password to clipboard (password)"
pbcopy "password"
pg_restore -U postgres -d memgpt -h localhost -p 8888 --no-owner --role=test_user < db.dump

psql $TEST_DB -c "ALTER DATABASE test_db SET SEARCH_PATH TO memgpt;"

rm db.dump

export DATABASE_URL=$TEST_DB