# set base image (host OS)
FROM python:3.10-bookworm

# set the working directory in the container
WORKDIR /code

# install dependencies
RUN apt update
RUN apt install -y sqlite3
RUN pip install pip --upgrade

# copy the dependencies file to the working directory
COPY requirements.txt /code
RUN pip install -r "requirements.txt"

# Copy local libraries
COPY test-gradio.py /code
COPY img/ /code/img

# expose a port for Gradio
EXPOSE 80

# command to run on container start
CMD [ "python3", "test-gradio.py" ]