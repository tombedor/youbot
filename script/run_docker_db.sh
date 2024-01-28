curl -L "https://raw.githubusercontent.com/cpacker/MemGPT/main/db/Dockerfile.simple" > Dockerfile.simple

# build container
docker build -f ./Dockerfile.simple -t memgpt_db .

# run container
docker run -d --rm \
   --name memgpt_db \
   -p 8888:5432 \
   -e POSTGRES_PASSWORD=password \
   -v memgpt_db_test:/var/lib/postgresql/data \
    memgpt_db:latest