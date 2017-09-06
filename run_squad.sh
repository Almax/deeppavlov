#!/usr/bin/env bash
python3 utils/train_model.py -t squad \
                         -m deeppavlov.agents.squad.squad:SquadAgent \
                         --batchsize 32 \
                         --display-examples False \
                         --max-train-time -1 \
                         --num-epochs -1 \
                         --log-every-n-secs 60 \
                         --log-every-n-epochs -1 \
                         --validation-every-n-secs -1 \
                         --validation-every-n-epochs 1 \
                         --chosen-metric f1 \
                         --validation-patience 5 \
                         --lr-drop-patience 1 \
                         --model-file '../save/squad/squad_6sept2017/fastqa_drqa' \
                         --pretrained_model '../save/squad/squad_6sept2017/fastqa_drqa' \
                         --embedding_file '/home/anatoly/data/fasttext/wiki-news-300d-1M.vec' 