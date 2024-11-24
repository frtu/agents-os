ARG STACK_VERSION=8.15.4

FROM docker.elastic.co/elasticsearch/elasticsearch:${STACK_VERSION}

# https://elk-docker.readthedocs.io/#installing-elasticsearch-plugins
RUN elasticsearch-plugin install --batch analysis-icu
RUN elasticsearch-plugin install --batch analysis-phonetic
RUN elasticsearch-plugin list
