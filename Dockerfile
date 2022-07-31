# Huggingface images: https://hub.docker.com/u/huggingface
# Huggingface dockerfiles: https://github.com/huggingface/transformers/tree/main/docker
FROM huggingface/transformers-pytorch-gpu:4.19.2 as release

WORKDIR /app

# https://github.com/HHousen/TransformerSum
# Download pretrained model
# https://stackoverflow.com/questions/25010369/wget-curl-large-file-from-google-drive
RUN pip install gdown
# Shifted download into app.py
# RUN gdown https://drive.google.com/uc?id=1VNoFhqfwlvgwKuJwjlHnlGcGg38cGM-- -O model.ckpt

# Install libraries specific to transformersum
RUN pip install scikit-learn tensorboard spacy sphinx pyarrow pre-commit pytorch_lightning torch_optimizer wandb rouge-score packaging datasets gradio

# Install app specific libraries
COPY requirements.txt ./
RUN pip install -r ./requirements.txt

# Show installed libraries
RUN pip freeze > frozen-requirements.txt

# Run code
COPY transformersum/src ./transformersum
COPY src ./
# Run unbuffered: https://stackoverflow.com/questions/55200135/python-docker-container-use-print
CMD stdbuf -oL python3 -u /app/app.py
