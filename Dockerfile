FROM python:3.8-slim AS aiocore

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ADD ./requirements.txt /

RUN apt-get update -y && \
    apt-get install -y gcc git build-essential libtool libicu-dev automake apt-utils pkg-config &&\
    pip install --upgrade pip && \
    pip3 install Cython &&\
    pip3 install git+https://github.com/MagicStack/uvloop &&\
    pip install --no-cache-dir -r requirements.txt &&\
    apt-get remove -y gcc && apt-get remove -y git && apt-get -y autoremove

FROM python:3.8-slim AS buildimage
COPY --from=aiocore /opt/venv /opt/venv
#ENV PATH=/root/.local:$PATH


FROM aiocore as search_svc
COPY --from=buildimage /opt/venv /opt/venv
COPY search_svc /aioget/search_svc
COPY core /aioget/core
COPY configs /aioget/configs
ENV PATH="/opt/venv/bin:$PATH"
CMD ['source', "$VIRTUAL_ENV/bin/activate"]


FROM aiocore as download_svc
COPY --from=buildimage /opt/venv /opt/venv
COPY download_svc /aioget/download_svc
COPY parser_scripts /aioget/parser_scripts
COPY core /aioget/core
COPY configs /aioget/configs
#ENV PATH="/opt/venv/bin:$PATH"
CMD ['source', "$VIRTUAL_ENV/bin/activate"]



FROM aiocore as parser_svc
COPY --from=buildimage /opt/venv /opt/venv
COPY parser_svc /aioget/parser_svc
COPY parser_scripts /aioget/parser_scripts
COPY core /aioget/core
COPY configs /aioget/configs
#ENV PATH="/opt/venv/bin:$PATH"
CMD ['source', "$VIRTUAL_ENV/bin/activate"]


FROM aiocore as logging_svc
COPY --from=buildimage /opt/venv /opt/venv
COPY logging_svc /aioget/logging_svc
COPY core /aioget/core
COPY configs /aioget/configs
#ENV PATH="/opt/venv/bin:$PATH"
CMD ['source', "$VIRTUAL_ENV/bin/activate"]
