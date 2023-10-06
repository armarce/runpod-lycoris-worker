FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-devel as base
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/London

RUN apt update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt update && \
    apt-get install -y git curl libgl1 libglib2.0-0 libgoogle-perftools-dev \
    python3.10-dev python3.10-tk python3-html5lib python3-apt python3-pip python3.10-distutils && \
    rm -rf /var/lib/apt/lists/*

# Set python 3.10 and cuda 11.8 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 3 && \
    update-alternatives --set python3 /usr/bin/python3.10 && \
    update-alternatives --set cuda /usr/local/cuda-11.7

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

WORKDIR /workspace

RUN mkdir sd-models

WORKDIR /workspace/sd-models

RUN wget https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned.safetensors

WORKDIR /workspace

RUN python3 -m pip install wheel

# Todo: Install torch 2.1.0 for cu121 support (only available as nightly as of writing)
## RUN python3 -m pip install --pre torch ninja setuptools --extra-index-url https://download.pytorch.org/whl/nightly/cu121

# Todo: Install xformers nightly for Torch 2.1.0 support
## RUN python3 -m pip install -v -U git+https://github.com/facebookresearch/xformers.git@main#egg=xformers

RUN git clone https://github.com/bmaltais/kohya_ss

WORKDIR /workspace/kohya_ss

COPY src/. .

RUN python3 -m pip install -r ./requirements_linux_docker.txt
RUN python3 -m pip install -r ./requirements.txt
RUN python3 -m pip install runpod
RUN python3 -m pip install boto3

# Replace pillow with pillow-simd
RUN python3 -m pip uninstall -y pillow && \
    CC="cc -mavx2" python3 -m pip install -U --force-reinstall pillow-simd

# Fix missing libnvinfer7
USER root
RUN ln -s /usr/lib/x86_64-linux-gnu/libnvinfer.so /usr/lib/x86_64-linux-gnu/libnvinfer.so.7 && \
    ln -s /usr/lib/x86_64-linux-gnu/libnvinfer_plugin.so /usr/lib/x86_64-linux-gnu/libnvinfer_plugin.so.7

RUN useradd -m -s /bin/bash appuser

WORKDIR /

RUN chown -R appuser: /workspace/kohya_ss

WORKDIR /workspace/kohya_ss

USER appuser

STOPSIGNAL SIGINT
ENV LD_PRELOAD=libtcmalloc.so
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
ENV PATH="$PATH:/home/appuser/.local/bin"

WORKDIR /workspace/kohya_ss
CMD python3 -u handler.py