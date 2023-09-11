# From https://github.com/jupyter/docker-stacks/wiki/Docker-recipes#add-a-python-2x-environment

# Choose your desired base image: you could use another from https://github.com/busbud/jupyter-docker-stacks
FROM jupyter/minimal-notebook:python-3.8

USER root
# RUN apt update
# RUN apt install -y pkg-config
# RUN apt install -y tk
# RUN apt install -y libfreetype6-dev
# RUN apt install -y libpng-dev
# # RUN apt install -y g++
# RUN apt install -y gcc
# USER root

# ffmpeg for matplotlib anim & dvipng for latex labels
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y build-essential && \
    apt-get install -y --no-install-recommends apt-utils && \
    apt-get install -y --no-install-recommends ffmpeg dvipng && \
    apt install -y graphviz &&\
    rm -rf /var/lib/apt/lists/*

# Create a Python 2.x environment using conda including at least the ipython kernel
# and the kernda utility. Add any additional packages you want available for use
# in a Python 2 notebook to the first line here (e.g., pandas, matplotlib, etc.)
RUN conda create --quiet --yes -p $CONDA_DIR/envs/python2 python=2.7 ipython ipykernel kernda freetype libpng tk && \
    conda clean -tip

# Bundle requirements
# You can change the libraries in the file
# requirements.txt
ADD requirements.txt /requirements.txt

# Create a global kernelspec in the image and modify it so that it properly activates
# the python2 conda environment.
RUN $CONDA_DIR/envs/python2/bin/python -m ipykernel install && \
    $CONDA_DIR/envs/python2/bin/kernda -o -y /usr/local/share/jupyter/kernels/python2/kernel.json && \
    pip install pkgconfig && \ 
    pip install freetype-py && \ 
    pip install pypng && \ 
    pip install setuptools==57.5.0 && \ 
    pip install -r /requirements.txt && \
    rm /requirements.txt

USER $NB_USER