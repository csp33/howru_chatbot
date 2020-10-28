FROM python:3.6.10-stretch
ENV PYTHONUNBUFFERED 1
# Copy config files
ADD config/requirements.txt /root/requirements.txt
ADD config/routes.json /etc/howru/cfg/routes.json
ADD config/initial_data.json /initial_data.json
# Install dependencies
RUN pip install -r /root/requirements.txt
# iPython for debugging
RUN pip3.6 install ipython
# Set workdir
WORKDIR /opt/web_interface

# Run server
CMD python3 manage.py makemigrations && \
    python3 manage.py migrate && \
 #   python3 manage.py loaddata /initial_data.json && \
    python3 manage.py runserver 0:8080
#CMD tail -f /dev/null
