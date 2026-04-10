FROM anujdatar/cups

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        ca-certificates \
        curl \
        git \
        python3 \
        unzip \
    && rm -rf /var/lib/apt/lists/*

COPY generate_tdp245_ppd.py /usr/local/bin/generate_tdp245_ppd.py


# Сборка и установка драйвера LBP810/1120
RUN git clone https://github.com/caxapyk/capt_lbp810-1120.git && \
    cd capt_lbp810-1120/capt-0.1 && \
    make CFLAGS="-O2 -g -DDEBUG" && \
    make install

# Install TSPL filters from the official Linux package and generate a
# single-purpose fixed label PPD from the filter-compatible SP410 profile.
RUN set -eux; \
    tmpdir="$(mktemp -d)"; \
    cd "$tmpdir"; \
    curl -L -o idprt.zip "https://www.idprt.com/prt_v2/files/down_file/id/283/fid/668.html"; \
    unzip -q idprt.zip; \
    case "$(dpkg --print-architecture)" in \
        amd64) filter_arch="x64" ;; \
        i386) filter_arch="x86" ;; \
        *) echo "unsupported TSPL driver architecture: $(dpkg --print-architecture)" >&2; exit 1 ;; \
    esac; \
    install -m 755 "idprt_tspl_printer_linux_driver_v1.4.7/filter/${filter_arch}/raster-tspl" /usr/lib/cups/filter/raster-tspl; \
    install -m 755 "idprt_tspl_printer_linux_driver_v1.4.7/filter/${filter_arch}/raster-esc" /usr/lib/cups/filter/raster-esc; \
    install -d -m 755 /usr/share/cups/model/tspl; \
    install -m 644 idprt_tspl_printer_linux_driver_v1.4.7/ppd/*.ppd /usr/share/cups/model/tspl/; \
    python3 /usr/local/bin/generate_tdp245_ppd.py \
        idprt_tspl_printer_linux_driver_v1.4.7/ppd/sp410.tspl.ppd \
        /usr/share/cups/model/tspl/TDP-245-fixed-tspl.ppd \
        30 \
        20 \
        2; \
    rm -rf "$tmpdir"
