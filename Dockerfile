FROM ubuntu:18.04
ENTRYPOINT []
RUN apt-get update && apt-get install -y python3 python3-pip && python3 -m pip install --no-cache --upgrade pip 
RUN pip3 install --no-cache rasa==1.10.11
RUN pip3 install --no-cache pika
ADD . /app/
RUN chmod +x /app/server.sh
CMD /app/server.sh
