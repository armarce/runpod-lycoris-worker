import runpod
import requests
import os
import shutil
import fnmatch
import math 
import subprocess
from s3 import S3
from renameImages import renameImages

def handler(job):

    S3(job['input']['s3']).testConnection()

    job_input = job['input']

    dataset_url = job_input['dataset_url']

    if not dataset_url:
            
        raise ValueError('Dataset url is required')

    train_batch_size = job_input['train_batch_size']

    if not train_batch_size:

        raise ValueError('train_batch_size is required')

    output_name = job_input['output_name']

    if not output_name:

        raise ValueError('output_name name is required')
    
    r = requests.get(dataset_url, allow_redirects=True)

    basePath = os.path.dirname(__file__) + '/train'

    zipFilepath = basePath + '/' + os.path.basename(dataset_url) 

    dirExtractPath = f"{basePath}/datasets/{output_name}/temp"

    open(zipFilepath, 'wb').write(r.content)

    shutil.unpack_archive(zipFilepath, dirExtractPath)

    totalImages = len(fnmatch.filter(os.listdir(dirExtractPath), '*.*'))

    if totalImages < 10: 

        raise ValueError('Dataset must have at least 10 images')

    repeats = int(math.ceil(1200 / totalImages))

    groups = int(math.ceil(totalImages/train_batch_size))

    lr_scheduler_num_cycles = math.ceil(( 250 *  train_batch_size * groups ) / ( totalImages * repeats))

    steps = int( (totalImages * repeats * lr_scheduler_num_cycles) / ( train_batch_size * groups))

    datasetDir = f"{basePath}/datasets/{output_name}/{repeats}_{output_name}"

    #subprocess.run(f"mv {dirExtractPath} {datasetDir}", shell=True)

    os.rename(dirExtractPath, datasetDir)

    #subprocess.run(f"rm -r {datasetDir}/temp", shell=True)

    renameImages(datasetDir, train_batch_size, output_name)

    cmdLycoris = f'''accelerate launch --num_cpu_threads_per_process=4 "/workspace/sd-scripts/train_network.py" \
--enable_bucket --pretrained_model_name_or_path="/workspace/sd-models/v1-5-pruned.safetensors" \
--train_data_dir="{basePath}/datasets/{output_name}" --resolution="512,512" --output_dir="{basePath}/datasets/{output_name}" \
--logging_dir="{basePath}/logs" --network_alpha="16" \
--training_comment="trigger words: {output_name}" --save_model_as=safetensors \
--network_module=lycoris.kohya --network_args "conv_dim=8" "conv_alpha=4" "use_cp=False" "algo=loha" --network_dropout="0" \
--text_encoder_lr=0.0001 --unet_lr=0.0001 --network_dim=32 --gradient_accumulation_steps={groups} \
--output_name="{output_name}" --lr_scheduler_num_cycles="{lr_scheduler_num_cycles}" --lr_warmup="0" --no_half_vae \
--learning_rate="0.0001" --lr_scheduler="constant" --train_batch_size="{train_batch_size}" --max_train_steps="{steps}" \
--save_every_n_epochs="1" --mixed_precision="bf16" --save_precision="bf16" --cache_latents \
--cache_latents_to_disk --optimizer_type="Adamw" --max_data_loader_n_workers="0" \
--bucket_reso_steps=64 --min_snr_gamma=5 --xformers --bucket_no_upscale \
--multires_noise_iterations="6" --multires_noise_discount="0.2"'''

    subprocess.run(cmdLycoris, shell=True)

    safetensorPath = f'{basePath}/datasets/{output_name}/{output_name}.safetensors'

    S3(job['input']['s3']).uploadFile(safetensorPath)

    os.remove(zipFilepath)
    #subprocess.run(f"rm -r {datasetDir}", shell=True)
    shutil.rmtree(datasetDir)

    return {
        "totalImages": totalImages,
        "repeats": repeats,
        "groups": groups,
        "epochs": lr_scheduler_num_cycles,
        "steps": steps
    }

runpod.serverless.start({
    "handler": handler
})