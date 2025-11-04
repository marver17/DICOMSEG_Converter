FROM ubuntu:22.04

LABEL name="EUCAIM Annotation Converter"
LABEL version="1.4"
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
COPY src /usr/dicomconverter/src
COPY tests/roundtrip_validation.py /usr/dicomconverter/tests/roundtrip_validation.py
COPY tests/visualization_comparison.py /usr/dicomconverter/tests/visualization_comparison.py
COPY tests/algorithm_name_correction.py /usr/dicomconverter/tests/algorithm_name_correction.py
RUN conda tos accept --override-channels --channel defaults
RUN conda env create -n dicomseg --file /usr/dicomconverter/src/nifti/ENV.yml
RUN echo "source activate dicomseg" > ~/.bashrc
ENV BASH_ENV=~/.bashrc
RUN chmod +x /usr/dicomconverter/src/rtstruct/install_enviorment.sh
RUN /usr/dicomconverter/src/rtstruct/install_enviorment.sh
# Install validation dependencies in dicomseg environment
RUN conda run -n dicomseg pip install SimpleITK numpy scipy
# Make scripts executable
RUN chmod +x /usr/dicomconverter/src/run_scripts.sh
RUN chmod +x /usr/dicomconverter/src/csv_batch.py
RUN chmod +x /usr/dicomconverter/src/image_validation.py
RUN chmod +x /usr/dicomconverter/src/validation_wrapper.py
RUN chmod +x /usr/dicomconverter/tests/roundtrip_validation.py
RUN chmod +x /usr/dicomconverter/tests/visualization_comparison.py
RUN ln -s /usr/dicomconverter/src/run_scripts.sh /usr/dicomconverter/run_scripts
ENV PATH="${PATH}:/usr/dicomconverter/"
ENV PATH="${PATH}:/usr/dicomconverter/src/"
ENV PATH="${PATH}:/usr/dicomconverter/src/nifti/"
ENV PATH="${PATH}:/usr/dicomconverter/src/nifti/dcmqi-function/bin"
ENV PATH="${PATH}:/usr/dicomconverter/src/nifti/dicoseg2nifti"
ENV PATH="${PATH}:/usr/dicomconverter/src/rtstruct"
# Create logs directory with proper permissions (before switching user)
RUN mkdir -p /logs && chmod 777 /logs

# # create the user (and group) "ds"
RUN groupadd -g 1000 ds && \
    useradd --create-home --shell /bin/bash --uid 1000 --gid 1000 ds
# Default password "password" for ds user. 
RUN echo "ds:password" | chpasswd
USER ds:ds
RUN mkdir -p /home/ds/datasets && \
    mkdir -p /home/ds/persistent-home && \
    mkdir -p /home/ds/persistent-shared-folder

ENTRYPOINT ["/usr/dicomconverter/run_scripts"]


