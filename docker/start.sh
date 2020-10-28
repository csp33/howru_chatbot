#!/bin/zsh
./build_images.sh;
docker-compose -p "howru" up -d --remove-orphans --force-recreate