FROM ultravideo/kvazaar

RUN echo 'tzdata tzdata/Areas select Europe' | debconf-set-selections
RUN echo 'tzdata tzdata/Zones/Europe select Paris' | debconf-set-selections
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata && \
    apt-get -y install build-essential zlib1g-dev \
    libncurses5-dev libgdbm-dev libnss3-dev sqlite3 libsqlite3-dev \
    libssl-dev libreadline-dev libffi-dev curl software-properties-common && \
    rm -rf /var/lib/apt/lists/*

# RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
# RUN add-apt-repository ppa:deadsnakes/ppa
RUN mkdir /tmp/python-build && \
    cd /tmp/python-build && \
    curl -fsSL https://www.python.org/ftp/python/3.9.7/Python-3.9.7.tgz | tar zx --strip-components=1
RUN cd /tmp/python-build && \
    ./configure --enable-loadable-sqlite-extensions --enable-optimizations && \
    make -j "$(nproc)"
RUN cd /tmp/python-build && \
    make altinstall
RUN ln -s /usr/local/bin/python3.9 /usr/bin/python3.9
RUN python3.9 --version

RUN apt-get update \
    && apt-get install build-essential git curl ffmpeg python3-pip \
    zlib1g-dev libfreetype6-dev libjpeg62-dev libpng-dev libmad0-dev libfaad-dev libogg-dev libvorbis-dev libtheora-dev liba52-0.7.4-dev libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libavdevice-dev libxv-dev x11proto-video-dev libgl1-mesa-dev x11proto-gl-dev libxvidcore-dev libssl-dev libjack-dev libasound2-dev libpulse-dev libsdl2-dev dvb-apps mesa-utils \
    libpq-dev libsm6 libgl1 libxext6 -y

# RUN ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

WORKDIR /gpac-build
RUN git clone https://github.com/gpac/gpac.git
WORKDIR /gpac-build/gpac
RUN ./configure --static-bin
RUN make
RUN make install

WORKDIR /app

RUN python3.9 -m venv /venv
ENV PATH=/venv/bin:$PATH

COPY requirements.txt /app/
RUN pip install --upgrade setuptools pip 
RUN pip install scikit-build
RUN pip install --upgrade cmake
RUN python --version
RUN pip --version
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "/app/entrypoint.sh" ]
