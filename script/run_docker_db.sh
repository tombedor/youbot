# build container
docker build -f ./Dockerfile.simple -t memgpt_db .

docker run -d --rm \
   --name memgpt_db \
   -p 8888:5432 \
   -e POSTGRES_PASSWORD=password \
   -e MEMGPT_DB=memgpt_test \
   -v memgpt_db:/var/lib/postgresql/data \
    memgpt_db:latest