git pull
docker build . --tag squire:latest
docker run \
 --name squire \
 -v $PWD/logs:/squire/logs \
 -v $PWD/data:/squire/data \
 --restart unless-stopped \
 --network bots \
 squire