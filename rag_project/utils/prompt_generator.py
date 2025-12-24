"""Few-shot prompting module for RAG system."""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.retriever import RetrievalResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FewShotExample:
    """Few-shot example for prompting."""
    question: str
    answer: str
    context: Optional[str] = None


class FewShotPromptGenerator:
    """Generates prompts with few-shot examples for better LLM responses."""

    def __init__(self):
        """Initialize the prompt generator with examples from the domain."""
        self.examples = self._create_domain_examples()

    def _create_domain_examples(self) -> List[FewShotExample]:
        """Create few-shot examples from the folklore/epic domain with Chain-of-Thought reasoning."""
        return [
            FewShotExample(
                question="Кто такой Алпамыш?",
                answer="1. Сначала найду информацию об Алпамыше в контексте.\n2. В тексте упоминается, что Алпамыш — главный герой узбекского народного эпоса.\n3. Он описан как идеальный богатырь с необычайной силой и мужеством.\n4. Следовательно, Алпамыш — главный герой одноименного узбекского народного эпоса, представляющий собой образ идеального богатыря, защитника родного народа. Он обладает необычайной физической силой, мужеством и благородством.",
                context="Алпамыш является центральным персонажем узбекского эпического наследия."
            ),
            FewShotExample(
                question="Что такое народный эпос?",
                answer="1. Определю основные характеристики народного эпоса из контекста.\n2. Вижу, что эпос — это повествовательное произведение устного творчества.\n3. Он рассказывает о героических деяниях и исторических событиях.\n4. Эпос передается через устную традицию из поколения в поколение.\n5. Следовательно, народный эпос — это крупное повествовательное произведение устного народного творчества, рассказывающее о героических деяниях, важных исторических событиях и мифологических представлениях народа. Эпос передается из поколения в поколение через устную традицию и отражает национальный характер, ценности и культурные особенности народа.",
                context="Эпос является важной частью фольклорного наследия многих народов мира."
            )
        ]

    def generate_prompt(self, query: str, context: str,
                       include_examples: bool = True,
                       max_context_length: int = 2000) -> str:
        """
        Generate a few-shot prompt for the given query and context.

        Args:
            query: User's question
            context: Retrieved context from RAG
            include_examples: Whether to include few-shot examples
            max_context_length: Maximum length of context to include

        Returns:
            Formatted prompt string
        """
        # Truncate context if too long
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."

        prompt_parts = [
            "Ты эксперт по фольклору, эпосам и народным сказаниям. Ты помощник, который сначала размышляет, а потом отвечает. Всегда пиши свои шаги размышления, используя нумерованный список, затем дай окончательный ответ. Отвечай точно и информативно, основываясь на предоставленном контексте."
        ]

        if include_examples and self.examples:
            prompt_parts.append("\nВот примеры правильных ответов:")

            for example in self.examples:
                prompt_parts.append(f"\nQ: {example.question}")
                prompt_parts.append(f"A: {example.answer}")

        prompt_parts.extend([
            f"\nКонтекст: {context}",
            f"\nQ: {query}",
            "A:"
        ])

        return "\n".join(prompt_parts)

    def generate_structured_prompt(self, query: str, retrieval_results: List[RetrievalResult],
                                  max_context_length: int = 2000) -> Dict[str, Any]:
        """
        Generate a structured prompt with metadata for advanced LLM usage.

        Args:
            query: User's question
            retrieval_results: Results from RAG retrieval
            max_context_length: Maximum context length

        Returns:
            Dictionary with prompt components
        """
        # Build context from retrieval results
        context_parts = []
        source_documents = []

        for result in retrieval_results:
            context_parts.append(f"[Релевантность: {result.similarity_score:.3f}] {result.chunk.text}")
            source_documents.append({
                "document": result.chunk.document_title,
                "chunk_id": result.chunk.chunk_id,
                "similarity": result.similarity_score
            })

        full_context = "\n\n".join(context_parts)

        # Truncate if necessary
        if len(full_context) > max_context_length:
            full_context = full_context[:max_context_length] + "..."

        return {
            "system_message": "Ты эксперт по фольклору, эпосам и народным сказаниям. Ты помощник, который сначала размышляет, а потом отвечает. Всегда пиши свои шаги размышления, используя нумерованный список, затем дай окончательный ответ. Отвечай точно и информативно.",
            "few_shot_examples": [
                {"role": "user", "content": ex.question}
                for ex in self.examples
            ] + [
                {"role": "assistant", "content": ex.answer}
                for ex in self.examples
            ],
            "context": full_context,
            "query": query,
            "source_documents": source_documents,
            "prompt": self.generate_prompt(query, full_context, include_examples=True, max_context_length=max_context_length)
        }

    def add_example(self, question: str, answer: str, context: Optional[str] = None) -> None:
        """Add a new few-shot example."""
        new_example = FewShotExample(question=question, answer=answer, context=context)
        self.examples.append(new_example)
        logger.info(f"Added new few-shot example: {question[:50]}...")

    def remove_example(self, index: int) -> bool:
        """Remove an example by index."""
        if 0 <= index < len(self.examples):
            removed = self.examples.pop(index)
            logger.info(f"Removed example: {removed.question[:50]}...")
            return True
        return False

    def get_examples(self) -> List[FewShotExample]:
        """Get all current examples."""
        return self.examples.copy()

    def clear_examples(self) -> None:
        """Clear all examples."""
        self.examples.clear()
        logger.info("Cleared all few-shot examples")

    def generate_answer_template(self, query_type: str) -> str:
        """
        Generate an answer template based on query type.

        Args:
            query_type: Type of query ('who', 'what', 'where', 'when', 'how', 'why')

        Returns:
            Template string for consistent answer formatting
        """
        templates = {
            'who': "'{person}' — это {description}. {additional_info}",
            'what': "'{concept}' — это {definition}. {characteristics}",
            'where': "'{place}' находится {location}. {description}",
            'when': "'{event}' произошло {time}. {context}",
            'how': "'{process}' осуществляется следующим образом: {steps}",
            'why': "'{phenomenon}' происходит потому, что {reasons}"
        }

        return templates.get(query_type.lower(), "Ответ: {content}")

    def detect_query_type(self, query: str) -> str:
        """
        Detect the type of question to provide appropriate template.

        Args:
            query: User's question

        Returns:
            Query type string
        """
        query_lower = query.lower()

        if any(word in query_lower for word in ['кто такой', 'кто такая', 'кто это']):
            return 'who'
        elif any(word in query_lower for word in ['что такое', 'что это', 'что означает']):
            return 'what'
        elif any(word in query_lower for word in ['где находится', 'где', 'в каком месте']):
            return 'where'
        elif any(word in query_lower for word in ['когда', 'в какое время', 'в каком году']):
            return 'when'
        elif any(word in query_lower for word in ['как', 'каким образом', 'каким способом']):
            return 'how'
        elif any(word in query_lower for word in ['почему', 'зачем', 'по какой причине']):
            return 'why'
        else:
            return 'general'


class ContextualPromptGenerator(FewShotPromptGenerator):
    """Extended prompt generator with context-aware few-shot selection."""

    def __init__(self):
        """Initialize with extended examples."""
        super().__init__()
        self.examples.extend(self._create_additional_examples())

    def _create_additional_examples(self) -> List[FewShotExample]:
        """Create additional domain-specific examples with Chain-of-Thought reasoning."""
        return [
            FewShotExample(
                question="Какие подвиги совершил богатырь?",
                answer="1. Проанализирую информацию о богатырских подвигах в контексте.\n2. Вижу упоминания о защите родной земли и борьбе с врагами.\n3. Также говорится о победах над чудовищами и злыми духами.\n4. Отмечается освобождение пленников и восстановление справедливости.\n5. Следовательно, богатыри в эпосах совершали различные подвиги: защищали родную землю от врагов, побеждали чудовищ и злых духов, освобождали пленников, восстанавливали справедливость. Их подвиги символизировали борьбу добра со злом и защиту народных интересов.",
                context="Подвиги богатырей — центральная тема эпических произведений."
            ),
            FewShotExample(
                question="Что представляет собой устное народное творчество?",
                answer="1. Определю основные компоненты устного народного творчества.\n2. В контексте указано, что это произведения словесного искусства.\n3. Они создаются и передаются народом из уст в уста.\n4. Включает различные жанры: сказки, былины, песни, пословицы.\n5. Фольклор отражает культурные особенности народа.\n6. Следовательно, устное народное творчество (фольклор) — это совокупность произведений словесного искусства, создаваемых и передаваемых народом из уст в уста. Включает сказки, былины, песни, пословицы, поговорки, загадки. Фольклор отражает мировоззрение, историю и культуру народа.",
                context="Фольклор является основой культурного наследия народов."
            )
        ]

    def select_relevant_examples(self, query: str, max_examples: int = 2) -> List[FewShotExample]:
        """
        Select most relevant examples based on query content.

        Args:
            query: User's question
            max_examples: Maximum number of examples to select

        Returns:
            List of most relevant examples
        """
        if not self.examples:
            return []

        # Simple keyword-based relevance scoring
        query_words = set(query.lower().split())

        scored_examples = []
        for example in self.examples:
            example_words = set(example.question.lower().split()) | set(example.answer.lower().split())

            # Calculate relevance score based on word overlap
            overlap = len(query_words & example_words)

            # Boost score for question type similarity
            if self.detect_query_type(query) == self.detect_query_type(example.question):
                overlap += 1

            scored_examples.append((example, overlap))

        # Sort by relevance and return top examples
        scored_examples.sort(key=lambda x: x[1], reverse=True)

        return [example for example, _ in scored_examples[:max_examples]]

    def generate_adaptive_prompt(self, query: str, context: str,
                                max_context_length: int = 2000) -> str:
        """
        Generate an adaptive prompt with contextually relevant few-shot examples.

        Args:
            query: User's question
            context: Retrieved context
            max_context_length: Maximum context length

        Returns:
            Adaptive prompt string
        """
        relevant_examples = self.select_relevant_examples(query, max_examples=2)

        # Temporarily replace examples with relevant ones
        original_examples = self.examples.copy()
        self.examples = relevant_examples

        prompt = self.generate_prompt(query, context, include_examples=True,
                                    max_context_length=max_context_length)

        # Restore original examples
        self.examples = original_examples

        return prompt

    def generate_cot_prompt(self, query: str, context: str,
                           max_context_length: int = 2000) -> str:
        """
        Generate a Chain-of-Thought prompt with explicit reasoning instructions.

        Args:
            query: User's question
            context: Retrieved context
            max_context_length: Maximum context length

        Returns:
            CoT prompt string with step-by-step reasoning instructions
        """
        # Truncate context if too long
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."

        cot_instructions = """
Ты эксперт по фольклору, эпосам и народным сказаниям.

ВАЖНО: Следуй этой структуре ответа:
1. Сначала проанализируй предоставленный контекст
2. Найди ключевую информацию, относящуюся к вопросу
3. Сделай логические выводы на основе найденной информации
4. Дай окончательный ответ, основанный на твоем анализе

Пример желаемого поведения:
1. Сначала найду информацию о [предмет вопроса] в контексте.
2. В документе указано, что [ключевая информация].
3. На основе этого можно сделать вывод, что [логический вывод].
4. Следовательно, [окончательный ответ].
"""

        prompt_parts = [
            cot_instructions,
            f"\nКонтекст: {context}",
            f"\nВопрос: {query}",
            "\nОтвет (следуя структуре выше):"
        ]

        return "\n".join(prompt_parts)