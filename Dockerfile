FROM ultravideo/kvazaar

RUN echo 'tzdata tzdata/Areas select Europe' | debconf-set-selections
RUN echo 'tzdata tzdata/Zones/Europe select Paris' | debconf-set-selections
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata && \
    apt-get install -y software-properties-common && \
    rm -rf /var/lib/apt/lists/*
RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update \
    && apt-get install curl ffmpeg gpac python3.9 python3-pip python3.9-venv -y

WORKDIR /app

RUN python3.9 -m venv /venv
ENV PATH=/venv/bin:$PATH

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN python --version
RUN pip --version
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "/app/entrypoint.sh" ]
