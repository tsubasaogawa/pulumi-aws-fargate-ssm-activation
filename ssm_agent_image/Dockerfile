FROM ubuntu:20.04 AS downloader
LABEL maintainer "tsubasaogawa"

RUN apt update && apt install -y curl \
    && curl https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/debian_amd64/amazon-ssm-agent.deb \
       -o /usr/local/src/amazon-ssm-agent.deb \
    && curl https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 \
       -L -o /usr/local/bin/jq \
    && chmod 755 /usr/local/bin/jq

FROM ubuntu:20.04 AS main

COPY --from=downloader /usr/local/src/amazon-ssm-agent.deb /usr/local/src/
COPY --from=downloader /usr/local/bin/jq /usr/local/bin/
COPY --from=downloader /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
RUN dpkg -i /usr/local/src/amazon-ssm-agent.deb \
    && rm /usr/local/src/amazon-ssm-agent.deb \
    && cp /etc/amazon/ssm/seelog.xml.template /etc/amazon/ssm/seelog.xml \
    && jq '.Profile.ShareCreds |= false' /etc/amazon/ssm/amazon-ssm-agent.json.template > /etc/amazon/ssm/amazon-ssm-agent.json \
    && rm /usr/local/bin/jq

COPY entrypoint.sh /usr/local/bin/

CMD ["/bin/bash", "/usr/local/bin/entrypoint.sh"]
