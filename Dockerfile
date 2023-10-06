FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Africa/Johannesburg \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on

RUN apt update && \
    apt upgrade -y && \
    apt install -y git    

######################## Install NVIDIA CUDA ####################################

RUN apt update -y 
RUN apt install build-essential -y
RUN apt install nvidia-cuda-toolkit nvidia-cuda-toolkit-gcc -y

######################## Download repo kohya_ss/sd-scripts #######################

WORKDIR /workspace

RUN git clone https://github.com/kohya-ss/sd-scripts

WORKDIR /workspace/sd-scripts

RUN pip install -r requirements.txt
RUN pip install xformers==0.0.21 lion-pytorch==0.0.6 lycoris_lora==1.8.3 runpod boto3

#################################################################################

######################## Copy src files #########################################

COPY src/. .

######################## Move accelerate config file ###########################

RUN mkdir /root/.cache/huggingface/accelerate
RUN cp default_config.yaml /root/.cache/huggingface/accelerate

######################## Download SD model 1.5 Pruned (7.7 GB) ##################

WORKDIR /workspace/

RUN mkdir sd-models

WORKDIR /workspace/sd-models

RUN wget https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned.safetensors


#################################################################################

WORKDIR /workspace/sd-scripts
CMD python handler.py