# Stage 1: Base
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04 as base

ARG KOHYA_VERSION=v22.0.1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Africa/Johannesburg \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on \
    SHELL=/bin/bash

# Install Ubuntu packages
RUN apt update && \
    apt -y upgrade && \
    apt install -y --no-install-recommends \
        software-properties-common \
        python3.10-venv \
        python3-pip \
        python3-tk \
        bash \
        dos2unix \
        git \
        ncdu \
        net-tools \
        openssh-server \
        libglib2.0-0 \
        libsm6 \
        libgl1 \
        libxrender1 \
        libxext6 \
        ffmpeg \
        wget \
        curl \
        psmisc \
        rsync \
        vim \
        zip \
        unzip \
        p7zip-full \
        htop \
        pkg-config \
        libcairo2-dev \
        libgoogle-perftools4 libtcmalloc-minimal4 \
        apt-transport-https ca-certificates && \
    update-ca-certificates && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen

# Set Python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Stage 2: Install kohya_ss and python modules
FROM base as kohya_ss_setup

# Add SDXL base model
# This needs to already have been downloaded:
#   wget https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
RUN mkdir -p /sd-models
RUN cp /home/v1-5-pruned.safetensors /sd-models/v1-5-pruned.safetensors

# Create workspace working directory
WORKDIR /

# Install Kohya_ss
RUN git clone https://github.com/bmaltais/kohya_ss.git
WORKDIR /kohya_ss
RUN git checkout ${KOHYA_VERSION} && \
    python3 -m venv --system-site-packages venv && \
    source venv/bin/activate && \
    pip3 install torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 && \
    pip3 install runpod \ 
    pip install boto3 \ 
    pip3 install xformers==0.0.21 \
        bitsandbytes==0.41.1 \
        tensorboard==2.12.3 \
        tensorflow==2.12.0 \
        wheel \
        tensorrt && \
    pip3 install -r requirements.txt && \
    pip3 install . && \
    deactivate

WORKDIR /

# Copy scripts
COPY --chmod=755 pre_start.sh fix_venv.sh ./

# Copy accelerate configuration file
COPY accelerate.yaml ./

# Start the container

CMD [ "/pre_start.sh", "python3 -u /handler.py"]