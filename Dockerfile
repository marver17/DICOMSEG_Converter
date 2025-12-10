FROM ubuntu:24.04

LABEL name="EUCAIM Annotation Converter"
LABEL version="1.4"
LABEL authorization="Apache 2.0"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        wget \
        ca-certificates \
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

# Accept Conda terms of service and channels
RUN conda config --set always_yes true --set changeps1 false && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

RUN conda env create -n dicomseg --file /usr/dicomconverter/src/nifti/ENV.yml

# SECURITY: Verify dcmqi binaries integrity with SHA256 checksums
# This prevents use of tampered or corrupted binaries
WORKDIR /usr/dicomconverter/src/nifti/dcmqi-function/bin
RUN if [ -f SHA256SUMS ]; then \
        sha256sum -c SHA256SUMS && \
        echo "✓ dcmqi binaries verified successfully" || \
        (echo "✗ SECURITY ERROR: dcmqi binary verification FAILED!" && exit 1); \
    else \
        echo "⚠ WARNING: SHA256SUMS not found, skipping binary verification"; \
    fi
WORKDIR /

RUN echo "source activate dicomseg" > ~/.bashrc
ENV BASH_ENV=~/.bashrc
RUN chmod +x /usr/dicomconverter/src/rtstruct/install_enviorment.sh
RUN /usr/dicomconverter/src/rtstruct/install_enviorment.sh
# Install validation dependencies in dicomseg environment
RUN conda run -n dicomseg pip install SimpleITK numpy scipy dicom2nifti
# Make scripts executable
RUN chmod +x /usr/dicomconverter/src/run_scripts.sh \
    && chmod +x /usr/dicomconverter/src/csv_batch.py \
    && chmod +x /usr/dicomconverter/src/dicomseries2nifti.py \
    && chmod +x /usr/dicomconverter/src/image_validation.py \
    && chmod +x /usr/dicomconverter/src/validation_wrapper.py \
    && chmod +x /usr/dicomconverter/src/security/verify_binaries.sh \
    && chmod +x /usr/dicomconverter/tests/roundtrip_validation.py \
    && chmod +x /usr/dicomconverter/tests/visualization_comparison.py \
    && ln -s /usr/dicomconverter/src/run_scripts.sh /usr/dicomconverter/run_scripts
ENV PATH="${PATH}:/usr/dicomconverter/"
ENV PATH="${PATH}:/usr/dicomconverter/src/"
ENV PATH="${PATH}:/usr/dicomconverter/src/nifti/"
ENV PATH="${PATH}:/usr/dicomconverter/src/nifti/dcmqi-function/bin"
ENV PATH="${PATH}:/usr/dicomconverter/src/nifti/dicoseg2nifti"
ENV PATH="${PATH}:/usr/dicomconverter/src/rtstruct"

# SECURITY FIX: Create logs directory with proper permissions (755 instead of 777)
# This prevents unauthorized log manipulation while allowing ds user to write
RUN mkdir -p /logs && chmod 755 /logs

# Create the user (and group) "ds"
RUN groupadd -g 1000 ds && \
    useradd --create-home --shell /bin/bash --uid 1000 --gid 1000 ds

# SECURITY FIX: Removed hardcoded password
# Authentication should be handled at platform level (EUCAIM), not container level
# If password access is needed, use Docker secrets or Kubernetes secrets at runtime

# Change ownership of logs to ds user
RUN chown -R 1000:1000 /logs

# Create version file with build metadata
ARG VERSION=1.4.0
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=unknown
RUN echo "{\n\
  \"version\": \"${VERSION}\",\n\
  \"git_commit\": \"${GIT_COMMIT}\",\n\
  \"build_date\": \"${BUILD_DATE}\",\n\
  \"base_image\": \"ubuntu:22.04\"\n\
}" > /usr/dicomconverter/VERSION.json

# Switch to non-root user for security
USER ds:ds
RUN mkdir -p /home/ds/datasets && \
    mkdir -p /home/ds/persistent-home && \
    mkdir -p /home/ds/persistent-shared-folder

ENTRYPOINT ["/usr/dicomconverter/run_scripts"]


