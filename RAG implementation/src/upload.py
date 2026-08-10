from ipywidgets import widgets
from IPython.display import display


uploader = widgets.FileUpload(accept='.pdf', multiple=False, description="Upload PDF") 
display(uploader)


uploaded_files = uploader.value
if not uploaded_files:
    print("No file uploaded.")

if isinstance(uploaded_files, dict):
    uploaded_file =next(iter(uploaded_files.values())) 
    pdf_name= uploaded_file["metadata"] ["name"]
    

else:
    uploaded_file = uploaded_files [0]
    pdf_name = uploaded_file ["name"]

pdf_bytes = bytes(uploaded_file["content"])
print(f"Uploaded PDF: {pdf_name}")


pdf_chunks = load_and_chunk_pdf(pdf_bytes)
print("PDF loaded and chunked into", len (pdf_chunks), "chunks.")
print("First chunk preview:",
pdf_chunks [0][:200], "...") # Print first 200 characters of the first chunk