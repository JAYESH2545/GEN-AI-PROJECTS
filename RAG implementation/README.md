# 📄 PDF RAG Chatbot using Ollama, FAISS & Python

A Retrieval-Augmented Generation (RAG) chatbot that allows users to upload a PDF document and ask questions about its contents.

Instead of relying only on the knowledge stored inside the language model, this project retrieves relevant information from the uploaded PDF and uses it as context before generating an answer.

The project runs completely **locally** using **Ollama**, making it privacy-friendly and suitable for offline document question answering.

---

## Features

- Upload any PDF document
- Extract text from PDFs
- Split document into chunks
- Generate embeddings using Ollama
- Store embeddings in a FAISS vector database
- Retrieve the most relevant chunks for a query
- Generate context-aware answers using a local LLM
- Returns relevant responses based only on the uploaded document

---

## How RAG Works

```
                PDF
                 │
                 ▼
         Extract Text
                 │
                 ▼
          Chunk Document
                 │
                 ▼
      Generate Embeddings
        (Qwen Embedding)
                 │
                 ▼
      Store in FAISS Index
                 │
                 ▼
      User asks a Question
                 │
                 ▼
 Generate Query Embedding
                 │
                 ▼
 Search Similar Chunks
                 │
                 ▼
 Retrieved Context + Question
                 │
                 ▼
      Qwen LLM (Ollama)
                 │
                 ▼
            Final Answer
```

---

## Tech Stack

- Python
- Ollama
- Qwen 3 (1.7B)
- Qwen Embedding Model
- FAISS
- NumPy
- PyPDF
- Jupyter Notebook
- IPyWidgets

---

## Project Structure

```
RAG-PDF-CHATBOT/
│
├── README.md
├── requirements.txt
├── rag_chatbot.ipynb
└── sample.pdf
```

---

## Installation

### Clone the repository

```bash
git clone https://github.com/yourusername/RAG-PDF-Chatbot.git

cd RAG-PDF-Chatbot
```

### Create a virtual environment

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## Install Ollama

Download Ollama from

https://ollama.com/

Pull the required models

```bash
ollama pull qwen3:1.7b

ollama pull qwen3-embedding:latest
```

Start Ollama

```bash
ollama serve
```

---

## Usage

Run the notebook.

Upload any PDF.

The project will

- Read the PDF
- Split it into chunks
- Generate embeddings
- Store embeddings in FAISS

Then ask questions such as

```
What is this document about?

Summarize chapter 2.

List all Python topics.

What are the exam marks?

Explain Unit 4.
```

The chatbot retrieves relevant sections from the document and generates an answer using the local language model.

---

## Models Used

### Embedding Model

```
qwen3-embedding:latest
```

Used for converting text chunks and user queries into vector embeddings.

### Chat Model

```
qwen3:1.7b
```

Used to generate answers from the retrieved document context.

---

## Retrieval Pipeline

1. Upload PDF
2. Extract text
3. Split into chunks
4. Generate embeddings
5. Store embeddings in FAISS
6. Convert user question into embedding
7. Retrieve Top-K similar chunks
8. Pass retrieved chunks to Qwen
9. Generate final response

---

## Example

### User

```
What are the topics in Python?
```

### Retrieved Context

```
Unit 1:
Introduction to Python

Unit 2:
Functions

Unit 3:
Object-Oriented Programming

...
```

### AI Response

```
The Python syllabus includes:

• Introduction to Python
• Variables and Data Types
• Functions
• File Handling
• Object-Oriented Programming
• Exception Handling
• Modules
```

---

## Future Improvements

- Streamlit Web App
- Support multiple PDFs
- Persistent FAISS index
- Metadata filtering
- Better document chunking
- Conversation memory
- Source citations
- Hybrid search (BM25 + Vector Search)
- GPU acceleration

---

## Requirements

- Python 3.10+
- Ollama
- Qwen3 1.7B
- Qwen3 Embedding Model

---

## License

This project is developed for educational purposes. 