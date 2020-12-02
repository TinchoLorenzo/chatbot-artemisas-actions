FROM ubuntu:18.04
ENTRYPOINT []
RUN apt-get update && apt-get install -y python3 python3-pip && python3 -m pip install --no-cache --upgrade pip 
RUN pip3 install --no-cache rasa==2.0.0
RUN pip3 install --no-cache pika
RUN pip3 install --no-cache pymongo
RUN pip3 install --no-cache pymongo[srv]
ADD . /app/
RUN chmod +x /app/server.sh
CMD /app/server.sh
