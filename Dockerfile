FROM python:3.7.9-slim-buster
    
# Directory in container for all project files
ENV DOCKYARD_SRCHOME=/src

# Local directory with project source
ENV DOCKYARD_SRC=code/famsplit

# Directory in container for project source files
ENV DOCKYARD_SRVPROJ=$DOCKYARD_SRVHOME/$DOCKYARD_SRC

# Create application subdirectories
WORKDIR $DOCKYARD_SRVPROJ

RUN apt-get update
RUN apt-get install python3-dev default-libmysqlclient-dev gcc  -y
# Copy just requirements.txt
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install -r /tmp/requirements.txt --no-cache-dir

COPY . .

COPY ./entrypoint.sh /tmp/entrypoint.sh
RUN chmod a+x /tmp/entrypoint.sh
ENTRYPOINT ["/tmp/entrypoint.sh"]
