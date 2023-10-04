#!/usr/bin/env bash
export PYTHONUNBUFFERED=1
# Configure accelerate
echo "Configuring accelerate..."
mkdir -p /root/.cache/huggingface/accelerate
mv /accelerate.yaml /root/.cache/huggingface/accelerate/default_config.yaml
mkdir -p /workspace/logs
cd /workspace/kohya_ss
source venv/bin/activate