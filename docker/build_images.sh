#!/bin/zsh

# Chatbot
docker build -t psychologist-bot chatbot

# Web interface
docker build -t web_interface web_interface
docker build -t proxy proxy