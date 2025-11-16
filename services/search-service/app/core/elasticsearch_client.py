from elasticsearch import AsyncElasticsearch
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Elasticsearch mapping for movies index
MOVIES_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "autocomplete_analyzer": {
                    "type": "custom",
                    "tokenizer": "autocomplete_tokenizer",
                    "filter": ["lowercase", "asciifolding"]
                },
                "search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"]
                }
            },
            "tokenizer": {
                "autocomplete_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                    "token_chars": ["letter", "digit"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "movie_id": {
                "type": "keyword"
            },
            "title": {
                "type": "text",
                "analyzer": "autocomplete_analyzer",
                "search_analyzer": "search_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    },
                    "suggest": {
                        "type": "completion"
                    }
                }
            },
            "original_title": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "description": {
                "type": "text",
                "analyzer": "standard"
            },
            "year": {
                "type": "integer"
            },
            "duration": {
                "type": "integer"
            },
            "rating": {
                "type": "float"
            },
            "age_rating": {
                "type": "keyword"
            },
            "is_published": {
                "type": "boolean"
            },
            "published_at": {
                "type": "date"
            },
            "poster_url": {
                "type": "keyword",
                "index": False
            },
            "trailer_url": {
                "type": "keyword",
                "index": False
            },
            "imdb_id": {
                "type": "keyword"
            },
            "genres": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "slug": {"type": "keyword"}
                }
            },
            "actors": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "full_name": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "character_name": {"type": "text"}
                }
            },
            "directors": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "full_name": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    }
                }
            },
            "created_at": {
                "type": "date"
            },
            "updated_at": {
                "type": "date"
            }
        }
    }
}


class ElasticsearchClient:
    def __init__(self):
        self.client: AsyncElasticsearch | None = None

    async def connect(self):
        """Initialize Elasticsearch connection"""
        try:
            self.client = AsyncElasticsearch(
                hosts=settings.ELASTICSEARCH_HOSTS,
                timeout=settings.ELASTICSEARCH_TIMEOUT,
                max_retries=settings.ELASTICSEARCH_MAX_RETRIES,
                retry_on_timeout=True
            )

            # Check connection
            if await self.client.ping():
                logger.info("✅ Connected to Elasticsearch")

                # Create index if not exists
                await self.ensure_index()
            else:
                logger.error("❌ Failed to ping Elasticsearch")
        except Exception as e:
            logger.error(f"❌ Elasticsearch connection error: {e}")
            raise

    async def ensure_index(self):
        """Create movies index if it doesn't exist"""
        try:
            index_exists = await self.client.indices.exists(index=settings.ELASTICSEARCH_INDEX)

            if not index_exists:
                await self.client.indices.create(
                    index=settings.ELASTICSEARCH_INDEX,
                    body=MOVIES_INDEX_MAPPING
                )
                logger.info(f"✅ Created index: {settings.ELASTICSEARCH_INDEX}")
            else:
                logger.info(f"ℹ️  Index already exists: {settings.ELASTICSEARCH_INDEX}")
        except Exception as e:
            logger.error(f"❌ Error creating index: {e}")
            raise

    async def close(self):
        """Close Elasticsearch connection"""
        if self.client:
            await self.client.close()
            logger.info("🔌 Elasticsearch connection closed")

    def get_client(self) -> AsyncElasticsearch:
        """Get Elasticsearch client instance"""
        if not self.client:
            raise RuntimeError("Elasticsearch client not initialized. Call connect() first.")
        return self.client


# Global ES client instance
es_client = ElasticsearchClient()


async def get_es_client() -> AsyncElasticsearch:
    """Dependency to get ES client"""
    return es_client.get_client()
