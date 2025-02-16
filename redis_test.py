import redis

def test_redis_connection():
    try:
        # Create Redis client
        print("Connecting to Redis...")
        r = redis.Redis(
            host='redis-14704.c337.australia-southeast1-1.gce.redns.redis-cloud.com',
            port=14704,
            decode_responses=True,
            username="default",
            password="GxBvkdZUHBGuP64CINVu0K8LRj6HcPlz",
            db=0,
            retry_on_timeout=True,
            socket_timeout=10
        )
        
        # Test basic operations
        print("\nTesting basic operations:")
        success = r.set('foo', 'bar')
        print(f"Set operation successful: {success}")
        
        result = r.get('foo')
        print(f"Retrieved value: {result}")
        
        # Clean up
        r.delete('foo')
        print("\nTest completed successfully!")
        
    except redis.AuthenticationError:
        print("Authentication failed. Please check username and password.")
    except redis.ConnectionError as e:
        print(f"Connection failed: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    test_redis_connection() 