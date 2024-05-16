ROOT_USER="postgresql://postgres:password@localhost:8888/"


psql $ROOT_USER -c "DROP DATABASE IF EXISTS memgpt;"
psql $ROOT_USER -c "DROP ROLE IF EXISTS mempgt;"
psql $ROOT_USER -c "CREATE ROLE mempgt WITH LOGIN PASSWORD 'password';"
psql $ROOT_USER -c "CREATE DATABASE memgpt OWNER mempgt;"
export LOCAL_DB="postgresql://mempgt:password@localhost:8888/memgpt"
psql "postgresql://postgres:password@localhost:8888/memgpt" -c "CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;"



pg_dump $REMOTE_URL --format=custom > db.dump

echo "copying password to clipboard (password)"
echo "password" | pbcopy 
pg_restore -U postgres -d memgpt -h localhost -p 8888 --no-owner --role=mempgt < db.dump

psql "postgresql://postgres:password@localhost:8888/memgpt" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public to memgpt;"
# psql $LOCAL_DB -c "ALTER DATABASE memgpt SET SEARCH_PATH TO memgpt;"

rm db.dump

export DATABASE_URL=$LOCAL_DB