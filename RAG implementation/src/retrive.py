def retrive_relevant_chunks(query, top_k=8):
    query_embedding = embed_chunks([query])

    distance, indices = index.search(np.array(query_embedding).astype("float32"),top_k)
    relevant_chunks = [pdf_chunks[i]for i in indices[0]]

    return relevant_chunks


text_question = "What is this document about?"

found_chunks = retrive_relevant_chunks(text_question)

print("Found relevant chunks for the question:", text_question)

for i, chunk in enumerate(found_chunks, 1):
    print(f"Chunk {i} preview:", chunk[:200], "...") # print first 200 character of each releveant chunk
