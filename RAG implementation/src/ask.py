def ask_pdf(question, top_k=8):
    relevant_chunks = retrive_relevant_chunks(question, top_k)
    context = "\n\n---\n\n".join(relevant_chunks)

    prompt = f"""You are answering questions about a document using the excerpts below. Read all the excerpts carefully; the answer may be spread across multiple excerpts.

Excerpts:
{context}

Question:
{question}

Answer:
"""

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={"num_ctx": 4096}
    )

    return response["message"]["content"]


answer = ask_pdf("What is this document about?")
print("Answer:", answer)