import runpod
import requests
import os
import shutil
import fnmatch
import math 
import subprocess
from runpod.serverless.utils import rp_upload

sleep_time = int(os.environ.get('SLEEP_TIME', 3))

## load your model(s) into vram here

def handler(job):

    job_input = job['input']

    dataset_url = job_input['dataset_url']

    train_batch_size = job_input['train_batch_size']

    output_name = job_input['output_name']

    r = requests.get(dataset_url, allow_redirects=True)

    basePath = os.path.dirname(__file__) + '/train'

    zipFilepath = basePath + '/' + os.path.basename(dataset_url) 

    dirExtractPath = basePath + '/datasets/' + job_input['output_name']

    open(zipFilepath, 'wb').write(r.content)

    shutil.unpack_archive(zipFilepath, dirExtractPath)

    totalImages = len(fnmatch.filter(os.listdir(dirExtractPath), '*.*'))

    repeats = int(math.ceil(1200 / totalImages))

    groups = int(math.ceil(totalImages/train_batch_size))

    lr_scheduler_num_cycles = math.ceil(( 250 *  train_batch_size * groups ) / ( totalImages * repeats))

    steps = int( (totalImages * repeats * lr_scheduler_num_cycles) / ( train_batch_size * groups))

    os.rename(dirExtractPath, "{}/datasets/{}_{}".format(basePath, repeats, output_name))

    cmdVenv = 'source venv/bin/activate'

    cmdLora = '''accelerate launch --num_cpu_threads_per_process=4 "./train_network.py" \
--enable_bucket --pretrained_model_name_or_path="runwayml/stable-diffusion-v1-5" \
--train_data_dir="{basePath}/datasets" --resolution="512,512" --output_dir="{basePath}/datasets" \
--logging_dir="{basePath}/logs" --network_alpha="16" \
--training_comment="trigger words: {output_name}" --save_model_as=safetensors \
--network_module=lycoris.kohya --network_args "conv_dim=8" "conv_alpha=4" "use_cp=False" "algo=loha" --network_dropout="0" \
--text_encoder_lr=0.0001 --unet_lr=0.0001 --network_dim=32 --gradient_accumulation_steps={groups} \
--output_name="{output_name}" --lr_scheduler_num_cycles="{lr_scheduler_num_cycles}" --lr_warmup="0" --no_half_vae \
--learning_rate="0.0001" --lr_scheduler="constant" --train_batch_size="{train_batch_size}" --max_train_steps="{steps}" \
--save_every_n_epochs="1" --mixed_precision="bf16" --save_precision="bf16" --cache_latents \
--cache_latents_to_disk --optimizer_type="Adamw" --max_data_loader_n_workers="0" \
--bucket_reso_steps=64 --min_snr_gamma=5 --xformers --bucket_no_upscale \
--multires_noise_iterations="6" --multires_noise_discount="0.2"'''.format(basePath = basePath, 
                                                                        groups = groups, 
                                                                        output_name = output_name, 
                                                                        lr_scheduler_num_cycles = lr_scheduler_num_cycles, 
                                                                        train_batch_size = train_batch_size,
                                                                        steps = steps
                                                                        )
    
    subprocess.run(cmdVenv, shell=True)
    subprocess.run(cmdLora, shell=True)

    safetensorPath = '{}/datasets/{}.safetensors'.format(basePath, output_name)

    safetensorUrl = rp_upload.upload_image('loras/{}.safetensors'.format(output_name), safetensorPath)

    os.remove(zipFilepath)
    os.remove(zipFilepath)

    return {
        "totalImages": totalImages,
        "repeats": repeats,
        "groups": groups,
        "lr_scheduler_num_cycles": lr_scheduler_num_cycles,
        "steps": steps,
        "safetensorUrl": safetensorUrl
    }

runpod.serverless.start({
    "handler": handler
})