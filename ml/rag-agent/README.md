# Build a RAG Agent

A small retrieval-augmented generation (RAG) pipeline built while solving the
[TensorTonic "Build a RAG Agent" project](https://www.tensortonic.com/projects/react-agent).
Full credit to TensorTonic for the tutorial.

RAG = the model looks information up in a document *before* it answers, instead
of answering from memory. This notebook shows a bare LLM inventing an answer,
then the same model answering correctly once it can retrieve from the document.

## Files

| File | What it is |
|------|------------|
| `build_a_rag_agent.ipynb` | The notebook: markdown explainers paired with code cells. |
| `document.txt` | The source text the agent searches (TensorTonic's About / Offerings / FAQ). |

## What the notebook does

1. **Bare LLM baseline**: ask "What domains do TensorTonic's coding problems cover?" with no retrieval, and watch the model guess.
2. **Build the pipeline**: load `document.txt`, split it with `RecursiveCharacterTextSplitter` (~512 chars, 64 overlap), embed each chunk, and index them in a Chroma vector store.
3. **Retrieve**: turn the question into a vector and pull the top-`k` nearest chunks by cosine distance; a text bar chart and a 2D embedding-space plot visualize the hits.
4. **Grounded prompting**: a system prompt forces the model to answer using *only* the retrieved chunks and cite them as `[chunk N]`.
5. **Compare & explore**: run the same question bare vs. RAG side by side, then ask follow-ups (including one not in the document, which RAG should refuse cleanly).

## Running it

The code cells call an OpenAI-compatible model gateway:

- Chat model: `google.gemma-3-4b-it`
- Embeddings: `amazon.titan-embed-text-v2:0`

They run as-is inside the TensorTonic sandbox, where `OPENAI_BASE_URL` and
`OPENAI_API_KEY` are provided. To run elsewhere, point those environment
variables at a compatible endpoint that serves those models (or swap the model
names for ones your endpoint exposes), then install the dependencies:

```bash
pip install langchain-openai langchain-chroma langchain-text-splitters \
            langchain-core chromadb matplotlib numpy
```

```bash
export OPENAI_BASE_URL="https://your-gateway/v1"
export OPENAI_API_KEY="..."
jupyter notebook build_a_rag_agent.ipynb
```

The committed notebook has no cell outputs; it was not executed outside the
TensorTonic sandbox.
