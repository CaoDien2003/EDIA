from langchain_community.document_loaders import PyPDFLoader


def load_pdf(file_path: str) -> list:
    return PyPDFLoader(file_path).load()
