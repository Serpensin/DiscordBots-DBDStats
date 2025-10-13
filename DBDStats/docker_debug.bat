docker build -t serpensin/dbdstats:debug .
docker run --env-file .env -it --rm --name dbdstats serpensin/dbdstats:debug