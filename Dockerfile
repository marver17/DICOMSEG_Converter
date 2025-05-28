FROM ubuntu:22.04


LABEL name="DicomSegConverter"
LABEL version="1.3"
LABEL authorization="Apache 2.0"

RUN apt-get update \
    && apt-get install -y build-essential \
   && apt-get install -y wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh 
ENV PATH=$CONDA_DIR/bin:$PATH
COPY nifti /usr/dicomconverter/nifti
COPY rtstruct /usr/dicomconverter/rtstruct
RUN conda env create -n dicomseg --file /usr/dicomconverter/nifti/ENV.yml
RUN echo "source activate dicomseg" > ~/.bashrc
ENV BASH_ENV=~/.bashrc
RUN chmod +x /usr/dicomconverter/rtstruct/install_enviorment.sh
RUN /usr/dicomconverter/rtstruct/install_enviorment.sh
COPY run_scripts.sh /usr/dicomconverter/run_scripts
ENV PATH="${PATH}:/usr/dicomconverter/"
ENV PATH="${PATH}:/usr/dicomconverter/nifti/"
ENV PATH="${PATH}:/usr/dicomconverter/nifti/dcmqi-function/bin"
ENV PATH="${PATH}:/usr/dicomconverter/nifti/dicoseg2nifti"
ENV PATH="${PATH}:/usr/dicomconverter/rtstruct"
ENV PATH="${PATH}:/usr/dicomconverter/nifti/dicoseg2nifti"
ENTRYPOINT ["run_scripts"]


