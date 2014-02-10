#!/bin/bash

# EVERY_N utterance is used for training
# EVERY_N=3    ->   we use one third of training data
export EVERY_N=1
export TEST_SETS="dev test"

# Directories set up
export KALDI_ROOT=/ha/projects/vystadial/lib/pykaldi-kronos-build
export DATA_ROOT=`pwd`/data_voip_cs  # expects subdirectories train + $TEST_SETS
export WORK=`pwd`/model_voip_cs
export EXP=`pwd`/model_voip_cs/exp
export TGT_MODELS=../../resources/asr/voip_cs/kaldi/last

# Specify paths to arpa models. Paths may not contain spaces.
# Specify build0 or build1 or build2, .. for building (zero|uni|bi)-gram LM.
export LMs="build0 build2"

# Use path to prebuilt dictionary or 'build' command in order to build dictionary
# export DICTIONARY="../../resources/lm/caminfo/dict"
export DICTIONARY="build"


# Borders for estimating LM model weight.
# LMW is tuned on development set and applied on test set.
export min_lmw=4
export max_lmw=15

# Number of states for phonem training
export pdf=1200

# Maximum number of Gaussians used for training
export gauss=19200

export train_mmi_boost=0.05

export mmi_beam=13.0
export mmi_lat_beam=7.0
