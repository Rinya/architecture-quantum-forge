"""Test script for Few-shot prompting functionality."""
import sys
import logging
from rag_system import RAGSystem
from utils.prompt_generator import FewShotPromptGenerator, ContextualPromptGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_prompt_generators():
    """Test the prompt generators directly."""
    print("=" * 60)
    print("Testing Few-shot Prompt Generators")
    print("=" * 60)

    # Test basic FewShotPromptGenerator
    print("\n1. Testing FewShotPromptGenerator:")
    basic_generator = FewShotPromptGenerator()

    test_context = "Алпамыш - главный герой узбекского народного эпоса."
    test_query = "Кто такой Алпамыш?"

    prompt = basic_generator.generate_prompt(test_query, test_context)
    print("Generated prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)

    # Test ContextualPromptGenerator
    print("\n2. Testing ContextualPromptGenerator:")
    contextual_generator = ContextualPromptGenerator()

    adaptive_prompt = contextual_generator.generate_adaptive_prompt(test_query, test_context)
    print("Generated adaptive prompt:")
    print("-" * 50)
    print(adaptive_prompt)
    print("-" * 50)

    # Test query type detection
    print("\n3. Testing query type detection:")
    test_queries = [
        "Кто такой Алпамыш?",
        "Что такое эпос?",
        "Где происходят события?",
        "Когда был создан эпос?",
        "Как звали героя?",
        "Почему Алпамыш стал героем?"
    ]

    for query in test_queries:
        query_type = basic_generator.detect_query_type(query)
        print(f"  '{query}' -> {query_type}")


def test_rag_integration():
    """Test Few-shot prompting and Chain-of-Thought integration with RAG system."""
    print("\n" + "=" * 60)
    print("Testing RAG System Integration")
    print("=" * 60)

    try:
        # Initialize RAG system
        print("Initializing RAG system...")
        rag = RAGSystem(use_adaptive_prompting=True)

        # Try to initialize from chunks file
        try:
            rag.initialize_from_chunks_file()
            print("RAG system initialized successfully!")
        except Exception as e:
            print(f"Could not initialize from chunks file: {e}")
            print("This is expected if embeddings haven't been generated yet.")
            print("Run 'python utils/prepare_data.py' first to generate embeddings.")
            return

        # Test basic answer generation
        print("\n1. Testing basic answer generation:")
        test_query = "Кто такой Алпамыш?"

        try:
            answer = rag.generate_answer(test_query)
            print(f"Query: {test_query}")
            print("Generated answer prompt:")
            print("-" * 50)
            print(answer)
            print("-" * 50)
        except Exception as e:
            print(f"Error generating answer: {e}")

        # Test Chain-of-Thought answer generation
        print("\n2. Testing Chain-of-Thought answer generation:")
        try:
            cot_answer = rag.generate_cot_answer(test_query)
            print(f"Query: {test_query}")
            print("Generated CoT prompt:")
            print("-" * 50)
            print(cot_answer)
            print("-" * 50)
        except Exception as e:
            print(f"Error generating CoT answer: {e}")

        # Test structured answer generation
        print("\n3. Testing structured answer generation:")
        try:
            structured = rag.generate_structured_answer(test_query)
            print(f"Query Type: {structured['query_type']}")
            print(f"Confidence: {structured['confidence']:.3f}")
            print(f"Total Results: {structured['total_results']}")
            print("Answer prompt preview:")
            print(structured['answer_prompt'][:300] + "...")
        except Exception as e:
            print(f"Error generating structured answer: {e}")

        # Test system stats
        print("\n4. Testing system statistics:")
        stats = rag.get_system_stats()
        print(f"Prompt Generator: {stats.get('prompt_generator', 'N/A')}")
        print(f"Adaptive Prompting: {stats.get('adaptive_prompting', 'N/A')}")
        print(f"Status: {stats.get('status', 'N/A')}")

    except Exception as e:
        print(f"Error testing RAG integration: {e}")


def main():
    """Main test function."""
    print("Few-shot Prompting Test Suite")
    print("=" * 60)

    # Test 1: Prompt generators directly
    test_prompt_generators()

    # Test 2: RAG system integration
    test_rag_integration()

    print("\n" + "=" * 60)
    print("Test completed!")
    print("\nTo fully test Few-shot prompting with RAG:")
    print("1. Run 'python utils/prepare_data.py' to generate embeddings")
    print("2. Run 'python rag_system.py' for interactive testing")
    print("3. Try commands: 'answer Кто такой Алпамыш?' or 'answer_detailed народный эпос'")


if __name__ == "__main__":
    main()