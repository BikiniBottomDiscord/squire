git pull
docker build . --tag squire:latest
docker run -d \
 --name squire \
 --network prod \
 -v $PWD/logs:/squire/logs \
 -v $PWD/data:/squire/data \
 --restart unless-stopped \
 squire