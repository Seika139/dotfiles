#!/usr/bin/env bash

# このファイルは環境プロファイルの選択例です。
# `cp 01_select_env.sample.bash 01_select_env.bash` を行い、
# `BDOT_ENV_PROFILE_FILES` に読み込みたいプロファイルファイル名（03_prof_b.bash など）を列挙してください。
#
# 例:
# BDOT_ENV_PROFILE_FILES=(
#     "02_prof_a.bash"
#     "03_prof_b.bash"
# )

# shellcheck disable=SC2034
BDOT_ENV_PROFILE_FILES=("02_sample_profile.bash")
