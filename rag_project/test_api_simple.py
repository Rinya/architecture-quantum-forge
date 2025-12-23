"""Simple test script for RAG System API without Unicode issues."""
import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("PASS - Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   System initialized: {data['system_initialized']}")
            print(f"   Uptime: {data['uptime_seconds']:.1f}s")
            return True
        else:
            print(f"FAIL - Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL - Health check error: {e}")
        return False


def test_search():
    """Test search endpoint."""
    print("\nTesting search endpoint...")

    payload = {
        "query": "Кто такой Алпамыш?",
        "top_k": 3,
        "min_similarity": 0.5
    }

    try:
        response = requests.post(
            f"{BASE_URL}/search",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print("PASS - Search successful")
            print(f"   Query: {data['query']}")
            print(f"   Results found: {data['total_found']}")
            print(f"   Processing time: {data['processing_time_ms']:.1f}ms")

            for i, result in enumerate(data['results'][:2], 1):
                print(f"   {i}. {result['document_title']} (score: {result['similarity_score']:.3f})")
                print(f"      Text: {result['text'][:100]}...")
            return True
        else:
            print(f"FAIL - Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"FAIL - Search error: {e}")
        return False


def test_answer():
    """Test answer generation endpoint."""
    print("\nTesting answer generation...")

    payload = {
        "query": "Что такое народный эпос?",
        "top_k": 3,
        "max_context_length": 1500,
        "use_fewshot": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/answer",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print("PASS - Answer generation successful")
            print(f"   Query: {data['query']}")
            print(f"   Query type: {data['query_type']}")
            print(f"   Confidence: {data['confidence']:.3f}")
            print(f"   Processing time: {data['processing_time_ms']:.1f}ms")
            print(f"   Answer prompt preview: {data['answer_prompt'][:200]}...")
            return True
        else:
            print(f"FAIL - Answer generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"FAIL - Answer generation error: {e}")
        return False


def test_cot_answer():
    """Test Chain-of-Thought answer generation."""
    print("\nTesting Chain-of-Thought answer generation...")

    payload = {
        "query": "Кто такой Алпамыш?",
        "top_k": 3,
        "max_context_length": 1500
    }

    try:
        response = requests.post(
            f"{BASE_URL}/answer/cot",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print("PASS - CoT answer generation successful")
            print(f"   Query: {data['query']}")
            print(f"   Query type: {data['query_type']}")
            print(f"   Confidence: {data['confidence']:.3f}")
            print(f"   Processing time: {data['processing_time_ms']:.1f}ms")
            print(f"   CoT prompt preview: {data['answer_prompt'][:200]}...")
            return True
        else:
            print(f"FAIL - CoT answer generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"FAIL - CoT answer generation error: {e}")
        return False


def test_documents():
    """Test documents listing endpoint."""
    print("\nTesting documents listing...")

    try:
        response = requests.get(f"{BASE_URL}/documents", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("PASS - Documents listing successful")
            print(f"   Total documents: {len(data)}")
            if data:
                print("   Sample documents:")
                for doc in data[:3]:
                    print(f"     - {doc}")
            return True
        else:
            print(f"FAIL - Documents listing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"FAIL - Documents listing error: {e}")
        return False


def test_stats():
    """Test system stats endpoint."""
    print("\nTesting system stats...")

    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("PASS - System stats successful")
            print(f"   Status: {data['status']}")
            print(f"   Prompt generator: {data['prompt_generator']}")
            print(f"   Adaptive prompting: {data['adaptive_prompting']}")
            print(f"   Total chunks: {data['total_chunks']}")
            print(f"   Unique documents: {data['unique_documents']}")
            if data.get('total_vectors'):
                print(f"   Total vectors: {data['total_vectors']}")
            return True
        else:
            print(f"FAIL - System stats failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"FAIL - System stats error: {e}")
        return False


def main():
    """Run all API tests."""
    print("RAG System API Test Suite")
    print("=" * 50)

    # Wait for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)

    tests = [
        ("Health Check", test_health),
        ("Search", test_search),
        ("Answer Generation", test_answer),
        ("Chain-of-Thought Answer", test_cot_answer),
        ("Documents Listing", test_documents),
        ("System Stats", test_stats),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"FAIL - {test_name} crashed: {e}")
            results.append((test_name, False))
        time.sleep(1)  # Brief pause between tests

    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"   {status} - {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("All tests passed! API is working correctly.")
    else:
        print(f"{total - passed} test(s) failed. Check the logs above.")

    print("\nYou can also test the API interactively at:")
    print("   http://localhost:8000/docs (Swagger UI)")
    print("   http://localhost:8000/redoc (ReDoc)")


if __name__ == "__main__":
    main()