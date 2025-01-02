from fastapi import APIRouter, UploadFile, HTTPException, File, Body, Path
from http import HTTPStatus
from langchain_text_splitters import TokenTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, RootModel, ConfigDict, Field
from typing import List, Union, Annotated
from dataclasses import dataclass
from rag.classic_rag import OllamaLLMConfig, ClassicRagModel

@dataclass
class Current:
    """Stores current combination of LLM + knowledge base"""
    rag_model: Union[ClassicRagModel, None]
    retriever: Union[BaseRetriever, None]

rag_models = {} #stores all LLMs
retrievers = {} #stores all retrievers (knowledge bases)
current = Current(rag_model=None, retriever=None)

model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

router = APIRouter(prefix='/api/v1')


class UploadResponse(BaseModel):
    message: str
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"message": "file {filename} is uploaded and indexed"}]}
    )

class CreateModelRequest(BaseModel):
    model_id: Annotated[str, Field(
        ...,
        title="Model ID",
        description="Название конфига"
    )]
    config: Annotated[OllamaLLMConfig, Field(
        ...,
        title="Model Config",
        description="Название модели Ollama и параметры генерации")]

class CreateModelResponse(BaseModel):
    message: str
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"message": "model {model_id} is created"}]}
    )

class SetModelRequest(BaseModel):
    rag_model_id: Annotated[str, Field(
        ...,
        title="Rag Model Id",
        description="Название конфига для LLM"
    )]
    retriever_id: Annotated[str, Field(
        ...,
        title="Knowledge Base Id",
        description="Название файла базы знаний"
    )]

class SetModelResponse(BaseModel):
    message: str
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"message": "model {rag_model_id} is set with knowledge base {retriever_id}"}]}
    )

class ModelQueryRequest(BaseModel):
    query: Annotated[str, Field(
        ...,
        title="Model Query",
        description="Вопрос для RAG"
    )]

class ModelQueryResponse(BaseModel):
    answer: str
    supporting_facts: List[int]
    model_config = ConfigDict(
        json_schema_extra={"examples": [{
            "answer": "Genji Hashimoto is Japanese racer and businessman",
            "supporting_facts": [0]
        }]}
    )

class ModelListItem(BaseModel):
    model_id: str
    config: OllamaLLMConfig
    model_config = ConfigDict(
        json_schema_extra={"examples": [{
            "model_id": "gemma2:2b",
            "config": {
                "model": "gemma2:2b",
                "temperature": 0.3,
                "top_k": 20,
                "num_predict": 128
            }
        }]}
    )

class ModelListResponse(RootModel):
    root: List[ModelListItem]

class KBListItem(BaseModel):
    retriever_id: str
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"retriever_id": "input.txt"}]}
    )

class KBListResponse(RootModel):
    root: List[KBListItem]

class ModelRemoveResponse(BaseModel):
    message: str
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"message": "Model '{model_id}' removed"}]}
    )

class KBRemoveResponse(BaseModel):
    message: str
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"message": "File '{file_id}' removed"}]}
    )


@router.post(
    "/upload_file",
    response_model=UploadResponse,
    status_code=HTTPStatus.CREATED,
    description="Загрузка текстового файла и создание базы знаний на основе его содержимого"
)
async def fit(file: Annotated[UploadFile, File(
    description='Текстовый файл, который будет использоваться в качестве базы знаний',
)]):
    """Upload a text file, and create a retriever out of it"""
    global retrievers, embeddings
    if file.filename in retrievers:
        raise HTTPException(status_code=422, detail="Knowledge base with same filename already exists")

    if file.content_type != "text/plain":
        raise HTTPException(
            status_code=400, detail="You should load only plain text files (e.g. '.txt')"
        )
    text = await file.read()
    text = text.decode("utf-8")

    splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=250)
    docs = [Document(i) for i in splitter.split_text(text)]
    db = await FAISS.afrom_documents(docs, embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 20})
    retrievers[file.filename] = retriever

    return UploadResponse(message=f"file {file.filename} is uploaded and indexed")

@router.post(
    "/create_model",
    response_model=CreateModelResponse,
    description="Создание и сохранение конфига отвечающей LLM с переданными параметрами"
)
async def create_model(request: Annotated[CreateModelRequest, Body(
    title="Create Model",
    example={
        "model_id": "gemma2:2b",
        "config": {
            "model": "gemma2:2b",
            "temperature": 0.3,
            "top_k": 20,
            "num_predict": 128
        }
    },
)]):
    global rag_models
    if request.model_id in rag_models:
        raise HTTPException(status_code=422, detail="Model with same id already exists")
    rag_models[request.model_id] = ClassicRagModel(request.config)
    return CreateModelResponse(message=f"model {request.model_id} is created")

@router.post(
    "/set_model",
    response_model=SetModelResponse,
    description="Выбор модели и базы знаний для ответов на вопросы"
)
async def set_model(request: Annotated[SetModelRequest, Body(
    title="Set Model",
    example={
        "rag_model_id": "gemma2:2b",
        "retriever_id": "input.txt"
    }
)]):
    global current, rag_models, retrievers
    try:
        rag_model = rag_models[request.rag_model_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="Model not found")
    try:
        retriever = retrievers[request.retriever_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    current = Current(
        rag_model=rag_model,
        retriever=retriever
    )
    return SetModelResponse(message=f"model {request.rag_model_id} is set with knowledge base {request.retriever_id}")

@router.post(
    "/invoke",
    response_model=ModelQueryResponse,
    description="Задать вопрос и получить ответ"
)
async def model_invoke(request: Annotated[ModelQueryRequest, Body(
    title="Invoke Model",
    example={
        "query": 'Who is Genji Hashimoto?'
    }
)]):
    global current
    if current.rag_model is None or current.retriever is None:
        raise HTTPException(status_code=405, detail="Model and knowledge base are not set yet")
    answer, supporting = current.rag_model.multi_hop_rag_invoke(prompt=request.query, retriever=current.retriever)
    return ModelQueryResponse(answer=answer, supporting_facts=supporting)

@router.get(
    "/list_models",
    response_model=ModelListResponse,
    description="Вернуть список всех сохраненных конфигов для LLM"
)
async def list_models():
    global rag_models
    response = []
    for rag_model_id, rag_model in rag_models.items():
        response.append(ModelListItem(model_id=rag_model_id, config=rag_model.config))
    # Реализуйте получения списка обученных моделей
    return ModelListResponse(root=response)

@router.get(
    "/list_files",
    response_model=KBListResponse,
    description="Вернуть список всех загруженных файлов"
)
async def list_retrievers():
    global retrievers
    response = []
    for retriever_id in retrievers.keys():
        response.append(KBListItem(retriever_id=retriever_id))
    # Реализуйте получения списка обученных моделей
    return KBListResponse(root=response)

@router.delete(
    "/remove_model/{rag_model_id}",
    response_model=ModelRemoveResponse,
    description="Удалить сохраненный конфиг LLM"
)
async def remove_model(rag_model_id: Annotated[str, Path(
    title="Model Id",
    example="gemma2:2b"
)]):
    global rag_models
    try:
        del rag_models[rag_model_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="Model does not exist")

    return ModelRemoveResponse(message=f"Model '{rag_model_id}' removed")

@router.delete(
    "/remove_file/{retriever_id}",
    response_model=ModelRemoveResponse,
    description="Удалить загруженный файл"
)
async def remove_retriever(retriever_id: Annotated[str, Path(
    title="File Id",
    example="input.txt"
)]):
    global retrievers
    try:
        del retrievers[retriever_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="File does not exist")

    return KBRemoveResponse(message=f"File '{retriever_id}' removed")

@router.delete(
    "/remove_all_models",
    response_model=List[ModelRemoveResponse],
    description="Удалить все сохраненный конфиги LLM"
)
async def remove_all_models():
    global rag_models
    response = []
    for rag_model_id in rag_models:
        response.append(ModelRemoveResponse(message=f"Model '{rag_model_id}' removed"))
    rag_models = {}
    return response

@router.delete(
    "/remove_all_files",
    response_model=List[ModelRemoveResponse],
    description="Удалить все загруженные файлы"
)
async def remove_all_files():
    global retrievers
    response = []
    for retriever_id in retrievers:
        response.append(KBRemoveResponse(message=f"File '{retriever_id}' removed"))
    retrievers = {}
    return response
