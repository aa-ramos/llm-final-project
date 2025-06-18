import fitz
import re
from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


def load_doc(filename):
    # Opening the file as read only
    file = open(filename, "r", encoding="utf-8")
    text = file.read()
    file.close()
    return text


class SplitMarkdownDocumentsLoader(BaseLoader):
    def __init__(self, documents):
        self.documents = documents

    def lazy_load(self):
        for doc in self.documents:
            yield doc


# Markdown files
def split_markdown_data():
    headers = [("##", "Section")]
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers, strip_headers=False
    )

    file_paths = [
        ("data/glossario.md", "glossario.md"),
        ("data/processo_compra_casa.md", "processo_compra_casa.md"),
        ("data/documentos_necessarios.md", "documentos_necessarios.md"),
        ("data/medidas_do_governo.md", "medidas_do_governo.md"),
        ("data/tabelas_imt_2025.md", "tabelas_imt_2025.md")
    ]

    all_chunks = []
    for path, filename in file_paths:
        content = load_doc(path)

        # Obter a primeira linha para usar como Document Title
        first_line = content.splitlines()[0] if content else ""
        documentTitle = (
            first_line.replace("#", "").strip() if first_line else "Sem Título"
        )

        md_file = re.sub(r"^# .+\n", "", content, count=1)

        chunks = splitter.split_text(md_file)
        for idx, chunk in enumerate(chunks):
            chunk.metadata["Document Title"] = documentTitle
            chunk.metadata["source_file"] = filename
            chunk.metadata["chunk_index"] = idx
        all_chunks.extend(chunks)

    return SplitMarkdownDocumentsLoader(all_chunks)


# PDF files
def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text


def split_pdf_data(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks = splitter.split_documents([Document(page_content=text)])
    return chunks