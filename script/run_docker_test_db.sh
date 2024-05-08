# build container
docker build -f ./Dockerfile.simple -t memgpt_db_test .

docker run -d --rm \
   --name memgpt_db_test \
   -p 8888:5432 \
   -e POSTGRES_PASSWORD=password \
   -e MEMGPT_DB=memgpt_test \
   -v memgpt_db_test:/var/lib/postgresql/data \
    memgpt_db_test:latest