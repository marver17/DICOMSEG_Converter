FROM ubuntu:20.04
COPY  dcmqi-function /usr/dcmqi
RUN apt-get update \
    && apt-get install -y build-essential \
   && apt-get install -y wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH
COPY ENV.yml ENV.yml
RUN conda env create -n dicomseg --file ENV.yml
RUN echo "source activate dicomseg" > ~/.bashrc
ENV BASH_ENV=~/.bashrc
ENV ENV_NAME=dicomseg
COPY dicomsegconv_2.sh /usr/dcmqi/bin/dicomsegconv.sh
COPY dicom_conversion.py /usr/dcmqi/bin/dcm2nifti.py
COPY dicomseg2nifti /usr/dicomseg2nifti
ENV PATH="${PATH}:/usr/dcmqi/bin"
ENV PATH="${PATH}:/usr/dicomseg2nifti"
COPY algorithm_name_correction.py /usr/dcmqi/bin/algorithm_name_correction.py

# ENTRYPOINT ["dicomsegconv.sh"]
