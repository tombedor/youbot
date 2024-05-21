set -e

# build container
docker build -f ./Dockerfile.simple -t youbot_db .

# Define the expected database URL
expected_database_url="postgresql://localhost:8888/youbot?user=youbot&password=password"

# Check if DATABASE_URL matches the expected value
if [[ "$DATABASE_URL" != "$expected_database_url" ]]; then
    echo "Error: DATABASE_URL does not match the expected value."
    echo "Expected: $expected_database_url"
    echo "Got: $DATABASE_URL"
    exit 1
fi

exeted_test_database_url="postgresql://localhost:8889/youbot_test?user=youbot_test&password=password"

# Check if TEST_DATABASE_URL matches the expected value
if [[ "$TEST_DATABASE_URL" != "$exeted_test_database_url" ]]; then
    echo "Error: TEST_DATABASE_URL does not match the expected value."
    echo "Expected: $exeted_test_database_url"
    echo "Got: $TEST_DATABASE_URL"
    exit 1
fi


docker run -d --rm \
   --name youbot \
   -p 8888:5432 \
   -e DB_PASSWORD=password \
   -e POSTGRES_PASSWORD=password \
   -e DB_NAME=youbot \
   -e DB_USER=youbot \
   -v youbot:/var/lib/postgresql/data \
    youbot_db:latest    

docker run -d --rm \
   --name youbot_test \
   -p 8889:5432 \
   -e DB_PASSWORD=password \
   -e POSTGRES_PASSWORD=password \
   -e DB_NAME=youbot_test \
   -e DB_USER=youbot_test \
   -v youbot_test:/var/lib/postgresql/data \
    youbot_db:latest
