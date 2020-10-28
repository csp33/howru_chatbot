FROM python:3.6.10-stretch

# Install requirements

ADD config/requirements.txt /root/requirements.txt
ADD config/routes.json /etc/howru/cfg/routes.json
RUN pip install -r /root/requirements.txt

# iPython for debugging
RUN pip3.6 install ipython

# Set PYTHONPATH

ENV PYTHONPATH /opt/chatbot

# Run bot

WORKDIR /opt/chatbot
CMD python3 manage.py makemigrations && \
    python3 manage.py migrate && \
    python3 chatbot/src/bot.py
#CMD    tail -f /dev/null
