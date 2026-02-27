"""
RAG Pipeline: Lecture Slides Integration

Provides ephemeral FAISS-based retrieval of relevant chunks from lecture slides.
Only activated when lecture_slides is provided in the state.
"""

import logging
from typing import Optional

from question_engine.state import QLCState

logger = logging.getLogger(__name__)


def rag_retrieve_node(state: QLCState) -> dict:
    """
    LangGraph node: Embed lecture slides and retrieve relevant chunks.

    Reads state.lecture_slides, chunks and embeds the text, then queries
    with a code-based summary to retrieve the top-k most relevant chunks.

    Updates state with:
    - rag_context: concatenated relevant chunks (str)

    If RAG fails for any reason (import error, embedding failure, etc.),
    logs a warning and continues without lecture context.
    """
    lecture_slides: Optional[str] = state.get("lecture_slides")
    if not lecture_slides:
        logger.info("RAG node: no lecture slides provided, skipping.")
        return {"rag_context": None}

    try:
        # Import here so missing faiss/langchain won't break the rest of the app
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        source_code: str = state.get("source_code", "")

        # Chunk the lecture slides
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = splitter.split_text(lecture_slides)

        if not chunks:
            logger.warning("RAG node: lecture slides produced no chunks.")
            return {"rag_context": None}

        logger.info("RAG node: created %d chunks from lecture slides", len(chunks))

        # Embed and store in ephemeral FAISS index
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = FAISS.from_texts(chunks, embeddings)

        # Query with a brief summary of the student's code
        query = f"Python programming concepts related to:\n{source_code[:500]}"
        docs = vector_store.similarity_search(query, k=3)

        if not docs:
            logger.info("RAG node: no relevant chunks found.")
            return {"rag_context": None}

        rag_context = "\n\n---\n\n".join(doc.page_content for doc in docs)
        logger.info("RAG node: retrieved %d chunks for context", len(docs))
        return {"rag_context": rag_context}

    except ImportError as e:
        logger.warning("RAG node: required package not installed (%s). Skipping RAG.", e)
        return {"rag_context": None}
    except Exception as e:
        logger.warning("RAG node: retrieval failed (%s). Continuing without lecture context.", e)
        return {"rag_context": None}
