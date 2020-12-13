FROM ubuntu:20.04 AS downloader
LABEL maintainer "tsubasaogawa"

RUN apt-get update && apt-get install -y \
    curl \
    && curl https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/debian_amd64/amazon-ssm-agent.deb \
    -o /usr/local/src/amazon-ssm-agent.deb

FROM ubuntu:20.04 AS main

COPY --from=downloader /usr/local/src/amazon-ssm-agent.deb /usr/local/src/
RUN dpkg -i /usr/local/src/amazon-ssm-agent.deb \
    && rm /usr/local/src/amazon-ssm-agent.deb

COPY entrypoint.sh /usr/local/bin/

CMD ["/bin/bash", "/usr/local/bin/entrypoint.sh"]
