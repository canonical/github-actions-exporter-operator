FROM ubuntu:jammy as builder

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LC_LANG=C.UTF-8

WORKDIR /srv/

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        git-core \
        golang \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && git clone https://github.com/cpanato/github_actions_exporter.git \
    && cd github_actions_exporter \
    && make build \
    && ls -altr /srv/

FROM ubuntu:jammy

COPY --from=builder /srv/github_actions_exporter/github-actions-exporter /usr/local/bin/

RUN groupadd -r gh_exporter \
    && useradd -r -g gh_exporter gh_exporter \
    && chmod +x /usr/local/bin/github-actions-exporter

USER gh_exporter

EXPOSE 9101

ENTRYPOINT ["/usr/local/bin/github-actions-exporter"]