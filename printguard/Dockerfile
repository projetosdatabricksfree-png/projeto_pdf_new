FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    libssl-dev \
    nlohmann-json3-dev \
    libqpdf-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpq-dev \
    libpqxx-dev \
    liblcms2-dev \
    mupdf-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN cmake -S /app -B /app/build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build /app/build -j"$(nproc)"

CMD ["/app/build/apps/cli/printguard-cli"]
