FROM alpine:latest

# Install dependencies for building ngIRCd and handling .tar.xz
RUN apk add --no-cache build-base curl xz

# Download and extract ngIRCd source (correct URL!)
RUN curl -L -o ngircd.tar.xz https://github.com/ngircd/ngircd/releases/download/rel-26/ngircd-26.tar.xz \
    && tar -xf ngircd.tar.xz \
    && cd ngircd-26 \
    && ./configure --with-pam=no --prefix=/usr \
    && make && make install \
    && cd .. && rm -rf ngircd*

# Copy config and MOTD files into the container
COPY ngircd.conf /etc/ngircd/ngircd.conf
COPY ngircd.motd /etc/ngircd/ngircd.motd

EXPOSE 6667

# Run the server in foreground
CMD ["ngircd", "--nodaemon"]

