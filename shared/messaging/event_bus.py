"""
Event Bus Abstraction Layer for STRATUM PROTOCOL
Provides unified interface for message publishing and consumption
Supports Kafka, RabbitMQ, and Redis backends
"""

import json
import asyncio
import os
from typing import Any, Callable, Dict, Optional, List
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime


class MessageBrokerType(str, Enum):
    """Supported message broker types"""
    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"
    REDIS = "redis"


class Message:
    """Standard message format across all brokers"""
    
    def __init__(
        self,
        topic: str,
        payload: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.topic = topic
        self.payload = payload
        self.key = key
        self.headers = headers or {}
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps({
            "topic": self.topic,
            "payload": self.payload,
            "key": self.key,
            "headers": self.headers,
            "timestamp": self.timestamp.isoformat()
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        return cls(
            topic=data["topic"],
            payload=data["payload"],
            key=data.get("key"),
            headers=data.get("headers", {}),
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class MessageBroker(ABC):
    """Abstract base class for message brokers"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to broker"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to broker"""
        pass
    
    @abstractmethod
    async def publish(self, message: Message) -> None:
        """Publish message to topic"""
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        topics: List[str],
        handler: Callable[[Message], None]
    ) -> None:
        """Subscribe to topics and handle messages"""
        pass


class KafkaMessageBroker(MessageBroker):
    """Kafka implementation of message broker"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumer = None
        self._running = False
    
    async def connect(self) -> None:
        """Connect to Kafka cluster"""
        try:
            from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
            
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            print(f"✅ Connected to Kafka at {self.bootstrap_servers}")
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Kafka"""
        self._running = False
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()
        print("✅ Disconnected from Kafka")
    
    async def publish(self, message: Message) -> None:
        """Publish message to Kafka topic"""
        if not self.producer:
            raise RuntimeError("Producer not connected")
        
        await self.producer.send(
            message.topic,
            value=message.payload,
            key=message.key.encode('utf-8') if message.key else None,
            headers=[(k, v.encode('utf-8')) for k, v in message.headers.items()]
        )
    
    async def subscribe(
        self,
        topics: List[str],
        handler: Callable[[Message], None]
    ) -> None:
        """Subscribe to Kafka topics"""
        from aiokafka import AIOKafkaConsumer
        
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id=f"stratum-consumer-{os.getpid()}"
        )
        await self.consumer.start()
        
        self._running = True
        try:
            async for msg in self.consumer:
                if not self._running:
                    break
                
                message = Message(
                    topic=msg.topic,
                    payload=msg.value,
                    key=msg.key.decode('utf-8') if msg.key else None,
                    headers={k: v.decode('utf-8') for k, v in msg.headers}
                )
                
                try:
                    await handler(message)
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
        finally:
            await self.consumer.stop()


class RedisMessageBroker(MessageBroker):
    """Redis Pub/Sub implementation of message broker"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None
        self._running = False
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            import redis.asyncio as aioredis
            
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            print(f"✅ Connected to Redis at {self.redis_url}")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        self._running = False
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        print("✅ Disconnected from Redis")
    
    async def publish(self, message: Message) -> None:
        """Publish message to Redis channel"""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        await self.redis_client.publish(
            message.topic,
            message.to_json()
        )
    
    async def subscribe(
        self,
        topics: List[str],
        handler: Callable[[Message], None]
    ) -> None:
        """Subscribe to Redis channels"""
        await self.pubsub.subscribe(*topics)
        
        self._running = True
        try:
            async for redis_msg in self.pubsub.listen():
                if not self._running:
                    break
                
                if redis_msg["type"] == "message":
                    message = Message.from_json(redis_msg["data"])
                    
                    try:
                        await handler(message)
                    except Exception as e:
                        print(f"❌ Error handling message: {e}")
        except Exception as e:
            print(f"❌ Subscription error: {e}")


class EventBus:
    """
    Unified event bus interface
    Factory pattern for creating appropriate broker instance
    """
    
    @staticmethod
    def create(
        broker_type: MessageBrokerType = MessageBrokerType.KAFKA,
        **config
    ) -> MessageBroker:
        """
        Create message broker instance
        
        Args:
            broker_type: Type of message broker to use
            **config: Broker-specific configuration
            
        Returns:
            MessageBroker instance
        """
        if broker_type == MessageBrokerType.KAFKA:
            bootstrap_servers = config.get(
                "bootstrap_servers",
                os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            )
            return KafkaMessageBroker(bootstrap_servers)
        
        elif broker_type == MessageBrokerType.REDIS:
            redis_url = config.get(
                "redis_url",
                os.getenv("REDIS_URL", "redis://localhost:6379")
            )
            return RedisMessageBroker(redis_url)
        
        else:
            raise ValueError(f"Unsupported broker type: {broker_type}")


# Example usage:
"""
from shared.messaging.event_bus import EventBus, Message, MessageBrokerType

# Create Kafka event bus
event_bus = EventBus.create(MessageBrokerType.KAFKA)
await event_bus.connect()

# Publish message
message = Message(
    topic="infrastructure.events",
    payload={"node_id": "POWER_001", "status": "critical"},
    key="POWER_001"
)
await event_bus.publish(message)

# Subscribe to topics
async def handle_message(message: Message):
    print(f"Received: {message.payload}")

await event_bus.subscribe(
    topics=["infrastructure.events", "sensor.data"],
    handler=handle_message
)

# Cleanup
await event_bus.disconnect()
"""
