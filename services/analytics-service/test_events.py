#!/usr/bin/env python3
"""
Test script to send sample viewing events to the analytics service

Usage:
    python test_events.py
"""

import requests
import json
import uuid
from datetime import datetime
import random
import time

# Configuration
API_BASE_URL = "http://localhost:8006/api/v1"

# Sample data
SAMPLE_USERS = [str(uuid.uuid4()) for _ in range(10)]
SAMPLE_MOVIES = [str(uuid.uuid4()) for _ in range(20)]


def create_viewing_event(user_id, movie_id, event_type, position_seconds=0):
    """Send viewing event to analytics service"""
    url = f"{API_BASE_URL}/analytics/events"

    payload = {
        "user_id": user_id,
        "movie_id": movie_id,
        "event_type": event_type,
        "position_seconds": position_seconds,
        "session_id": str(uuid.uuid4()),
        "metadata": {
            "device": random.choice(["mobile", "desktop", "tv"]),
            "quality": random.choice(["720p", "1080p", "4k"]),
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Created {event_type} event: user={user_id[:8]}, movie={movie_id[:8]}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")


def simulate_viewing_session(user_id, movie_id):
    """Simulate a complete viewing session"""
    print(f"\n📺 Simulating viewing session...")

    # Start event
    create_viewing_event(user_id, movie_id, "start", 0)
    time.sleep(0.5)

    # Progress events
    for position in [300, 900, 1800, 3600]:  # 5min, 15min, 30min, 1hr
        create_viewing_event(user_id, movie_id, "progress", position)
        time.sleep(0.5)

    # Finish event (80% chance to finish)
    if random.random() > 0.2:
        create_viewing_event(user_id, movie_id, "finish", 5400)  # 90 minutes
        time.sleep(0.5)


def generate_sample_data(num_sessions=20):
    """Generate sample viewing data"""
    print(f"🚀 Generating {num_sessions} viewing sessions...")
    print(f"   Users: {len(SAMPLE_USERS)}")
    print(f"   Movies: {len(SAMPLE_MOVIES)}")

    for i in range(num_sessions):
        user_id = random.choice(SAMPLE_USERS)
        movie_id = random.choice(SAMPLE_MOVIES)

        simulate_viewing_session(user_id, movie_id)

    print(f"\n✅ Generated {num_sessions} viewing sessions!")


def test_analytics_endpoints():
    """Test analytics endpoints"""
    print("\n📊 Testing Analytics Endpoints...\n")

    # Test popular content
    print("1. Popular Content (last 7 days):")
    response = requests.get(f"{API_BASE_URL}/analytics/content/popular?days=7&limit=10")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Found {data['total_items']} popular movies")
        for item in data['items'][:3]:
            print(f"      - Movie {item['movie_id'][:8]}: {item['total_views']} views")
    else:
        print(f"   ❌ Error: {response.status_code}")

    # Test user stats
    print("\n2. User Statistics:")
    user_id = SAMPLE_USERS[0]
    response = requests.get(f"{API_BASE_URL}/analytics/user/{user_id}/stats?days=30")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ User {user_id[:8]}:")
        print(f"      - Movies started: {data['movies_started']}")
        print(f"      - Movies finished: {data['movies_finished']}")
        print(f"      - Completion rate: {data['completion_rate']}%")
    else:
        print(f"   ❌ Error: {response.status_code}")

    # Test trends
    print("\n3. Viewing Trends (last 7 days):")
    response = requests.get(f"{API_BASE_URL}/analytics/trends?days=7")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Found {len(data['trends'])} days of data")
    else:
        print(f"   ❌ Error: {response.status_code}")

    # Test peak hours
    print("\n4. Peak Hours (last 7 days):")
    response = requests.get(f"{API_BASE_URL}/analytics/peak-hours?days=7")
    if response.status_code == 200:
        data = response.json()
        peak_hours_data = data.get('peak_hours', [])
        if peak_hours_data:
            sorted_hours = sorted(peak_hours_data, key=lambda x: x['events_count'], reverse=True)
            print(f"   ✅ Peak hour: {sorted_hours[0]['hour']}:00 ({sorted_hours[0]['events_count']} events)")
        else:
            print("   ℹ️  No peak hours data yet")
    else:
        print(f"   ❌ Error: {response.status_code}")


def check_health():
    """Check service health"""
    try:
        response = requests.get("http://localhost:8006/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service is {data['status']}")
            print(f"   ClickHouse: {data['clickhouse']}")
            print(f"   Kafka: {data['kafka']}")
            return True
        else:
            print(f"❌ Service unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("Analytics Service Test Script")
    print("=" * 60)

    # Check service health
    if not check_health():
        print("\n⚠️  Service is not running. Start it with:")
        print("   docker-compose up -d")
        print("   or")
        print("   python -m app.main")
        return

    print("\nChoose an option:")
    print("1. Generate sample data (20 viewing sessions)")
    print("2. Generate lots of data (100 viewing sessions)")
    print("3. Test analytics endpoints")
    print("4. Both (generate data + test)")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        generate_sample_data(20)
    elif choice == "2":
        generate_sample_data(100)
    elif choice == "3":
        test_analytics_endpoints()
    elif choice == "4":
        generate_sample_data(20)
        time.sleep(2)  # Wait for data to be processed
        test_analytics_endpoints()
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
