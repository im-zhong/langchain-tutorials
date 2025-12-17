# 2025/12/1
# zhangzhong
# https://docs.langchain.com/oss/python/integrations/document_loaders
# 这种教程的学习放到一个文件里面是最合适的，那么这种test in doc的方式也最合适了
# 相较于直接写一个脚本，只有main一个入口，这个每一个test都是一个入口，可以测试很多东西
# 同时所有的代码都放在一块，后面再回过头来也方便


from langchain_community.document_loaders.csv_loader import CSVLoader

# 这个东西依赖的langchain版本太低了！！！而且好垃圾的，不用
# from langchain_unstructured import UnstructuredLoader
from langchain_community.document_loaders import PyPDFLoader


def test_csv_loader():
    loader = CSVLoader(file_path="example.csv")

    documents = loader.load()
    print(documents)

    # For large datasets, lazily load documents
    for document in loader.lazy_load():
        print(document)


# doesn't work
# https://docs.langchain.com/oss/python/integrations/document_loaders/unstructured_file
# https://github.com/pdfminer/pdfminer.six
# def test_unstructured() -> None:
#     file_path = "mamba.pdf"
#     loader = UnstructuredLoader(file_path=file_path)
#     docs = loader.load()
#     print(docs[0])


# try pypdf
# https://docs.langchain.com/oss/python/integrations/document_loaders/pypdfloader
# https://github.com/py-pdf/pypdf
def test_pypdf() -> None:
    file_path = "mamba.pdf"
    loader = PyPDFLoader(file_path=file_path)
    docs = loader.load()
    print(docs[0])


# python pdf parser:
# https://www.reddit.com/r/learnpython/comments/denb7s/pdfminer_vs_pypdf2/
# https://github.com/py-pdf/benchmarks?tab=readme-ov-file
