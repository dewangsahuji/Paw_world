
from elasticsearch import AsyncElasticsearch

from app.core.config import settings

def get_elastic_client() -> AsyncElasticsearch:
    return AsyncElasticsearch(hosts=[settings.elasticsearch_url])
