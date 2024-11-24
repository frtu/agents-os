db-elasticsearch
===

ElasticSearch with Kibana

## Startup

### Enable default ES

```yaml
elasticsearch:
  image: ${ELASTICSEARCH_IMAGE}
```

### Enable ES with plugins

Add the desired plugin into `Dockerfile` :

* comment `image` tag
* uncomment in `docker-compose.yml`

```yaml
elasticsearch:
  build:
    dockerfile: ./Dockerfile
```

## Load data

Load data by running

```
python ./ingest-movies/create_and_fill_es.py
```

## Usage

### Option 1 - docker compose

Start with ```docker-compose up```

You will be able to have :

* elasticsearch : port ```9200```
* kibana : [http://localhost:5601/](http://localhost:5601/)
