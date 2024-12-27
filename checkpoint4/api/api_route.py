from fastapi import APIRouter, UploadFile, HTTPException
from http import HTTPStatus
from langchain_text_splitters import TokenTextSplitter
# from langchain.vectorstores import FAISS
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, RootModel
from typing import List, Union
from dataclasses import dataclass
from checkpoint4.rag.classic_rag import OllamaLLMConfig, ClassicRagModel


@dataclass
class Current:
    rag_model: Union[ClassicRagModel, None]
    retriever: Union[BaseRetriever, None]

rag_models = {}
retrievers = {}
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

class CreateModelRequest(BaseModel):
    model_id: str
    config: OllamaLLMConfig

class CreateModelResponse(BaseModel):
    message: str

class SetModelRequest(BaseModel):
    rag_model_id: str
    retriever_id: str

class SetModelResponse(BaseModel):
    message: str

class ModelQueryRequest(BaseModel):
    query: str

class ModelQueryResponse(BaseModel):
    answer: str
    supporting_facts: List[int]

class ModelListItem(BaseModel):
    model_id: str
    config: OllamaLLMConfig

class ModelListResponse(RootModel):
    root: List[ModelListItem]

class KBListItem(BaseModel):
    retriever_id: str

class KBListResponse(RootModel):
    root: List[KBListItem]

class ModelRemoveResponse(BaseModel):
    message: str

class KBRemoveResponse(BaseModel):
    message: str


@router.post("/upload_file", response_model=UploadResponse, status_code=HTTPStatus.CREATED)
async def fit(file: UploadFile):
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

@router.post("/create_model", response_model=CreateModelResponse)
async def create_model(request: CreateModelRequest):
    global rag_models
    if request.model_id in rag_models:
        raise HTTPException(status_code=422, detail="Model with same id already exists")
    rag_models[request.model_id] = ClassicRagModel(request.config)
    return CreateModelResponse(message=f"model {request.model_id}")

@router.post("/set_model", response_model=SetModelResponse)
async def set_model(request: SetModelRequest):
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

@router.post("/invoke", response_model=ModelQueryResponse)
async def model_invoke(request: ModelQueryRequest):
    global current
    if current.rag_model is None or current.retriever is None:
        raise HTTPException(status_code=405, detail="Model and knowledge base are not set yet")
    answer, supporting = current.rag_model.multi_hop_rag_invoke(prompt=request.query, retriever=current.retriever)
    return ModelQueryResponse(answer=answer, supporting_facts=supporting)

@router.get("/list_models", response_model=ModelListResponse)
async def list_models():
    global rag_models
    response = []
    for rag_model_id, rag_model in rag_models.items():
        response.append(ModelListItem(model_id=rag_model_id, config=rag_model.config))
    # Реализуйте получения списка обученных моделей
    return ModelListResponse(root=response)

@router.get("/list_files", response_model=KBListResponse)
async def list_retrievers():
    global retrievers
    response = []
    for retriever_id in retrievers.keys():
        response.append(KBListItem(retriever_id=retriever_id))
    # Реализуйте получения списка обученных моделей
    return KBListResponse(root=response)

@router.delete("/remove_model/{rag_model_id}", response_model=ModelRemoveResponse)
async def remove_model(rag_model_id: str):
    global rag_models
    try:
        del rag_models[rag_model_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="Model does not exist")

    return ModelRemoveResponse(message=f"Model '{rag_model_id}' removed")

@router.delete("/remove_file/{retriever_id}", response_model=ModelRemoveResponse)
async def remove_retriever(retriever_id: str):
    global retrievers
    try:
        del retrievers[retriever_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="File does not exist")

    return KBRemoveResponse(message=f"File '{retriever_id}' removed")

@router.delete("/remove_all_models", response_model=List[ModelRemoveResponse])
async def remove_all_models():
    global rag_models
    response = []
    for rag_model_id in rag_models:
        response.append(ModelRemoveResponse(message=f"Model '{rag_model_id}' removed"))
    rag_models = {}
    return response

@router.delete("/remove_all_files", response_model=List[ModelRemoveResponse])
async def remove_all_files():
    global retrievers
    response = []
    for retriever_id in retrievers:
        response.append(KBRemoveResponse(message=f"File '{retriever_id}' removed"))
    retrievers = {}
    return response
