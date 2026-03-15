FROM us-central1-docker.pkg.dev/my-project/workstation-images/codeoss/rstudio:codeoss-locked--rstudio-locked

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-pip \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

RUN Rscript -e 'install.packages(c("reticulate", "keras3"), repos="https://cran.r-project.org")'
