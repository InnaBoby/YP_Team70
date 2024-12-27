from langchain_ollama import ChatOllama
# from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.vectorstores.base import BaseRetriever
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import re
import json
from pydantic import BaseModel, RootModel, Field
from typing import List, Literal, Optional, Union
import logging


leave_only_json = re.compile(r'''(\{.+})''')
keys_mapping = {'source_title': re.compile(r'title'), 'source_sentence_id': re.compile(r'id$')}

class RagResponse(BaseModel):
    answer: str
    source_id: int

class DecomposeResponse(RootModel):
    root: List[str]

class LLMConfig(BaseModel):
    pass

class OllamaLLMConfig(LLMConfig):
    model: str
    temperature: Union[float, None] = Field(None)
    top_k: Union[int, None] = Field(None)
    top_p: Union[float, None] = Field(None)
    num_predict: Union[int, None] = Field(None)


class ClassicRagModel:

    """Classic RAG model for multi-hop question answering"""

    def __init__(self, config: LLMConfig):

        kwargs = {k: v for k, v in config.model_dump().items() if v is not None}
        self.llm = ChatOllama(**kwargs)

        self.config = config

        self.decompose_template = """
        Decompose the following question into multiple simple questions.
        Decomposed questions must be concrete, self-sufficient and very short.
        If the question can not be decomposed, just repeat the original question.
        AVOID ANY CONVERSATIONAL ANSWERS
        Example:
        Original Question: What administrative territorial entity is the owner of Ciudad Deportiva located?
        Decomposed Questions: ["Who is the owner of Ciudad Deportiva?",
        "Where is #1 located?"]
        
        Original Question: Who is the child of the founder of the company that distributed the film UHF?
        Decomposed Questions: ["What company distributed the film UHF?",
        "Who founded #1?",
        "Who is #2's child?"]
        
        Actual Data:
        Original Question: {question}
        Decomposed Questions:
        """
        self.rag_template = """
        You are an assistant for question-answering tasks.
        Use the following pieces of retrieved context to answer the CURRENT QUESTION.
        If you don't know the answer, just say "I DON'T KNOW".
        Use ten words maximum and keep the answer concise and concrete
        Main question: {main_question}
        Previous sub-questions: {prev_questions}
        
        Context: {context}
        CURRENT QUESTION: {subquestion}
        Use the following pieces of retrieved context to answer the CURRENT QUESTION.
        Reply with valid json.
        """
        self.final_answer_template = """
        You are an assistant for question-answering tasks.
        Use the following sub-questions and corresponding answers to answer the MAIN QUESTION.
        If you don't know the answer, just say "I DON'T KNOW".
        Use ten words maximum and keep the answer concise and concrete.
        Previous sub-questions: {answers}
        MAIN QUESTION: {original_question}
        Avoid any conversational answers.
        """

        self.decompose_prompt = PromptTemplate.from_template(self.decompose_template)
        self.rag_prompt = PromptTemplate.from_template(self.rag_template)
        self.final_answer_prompt = PromptTemplate.from_template(self.final_answer_template)

        self.decompose_chain = (
                self.decompose_prompt
                | self.llm.bind(format = DecomposeResponse.model_json_schema())
                | JsonOutputParser()
        )
        self.rag_chain = (
                self.rag_prompt
                | self.llm.bind(format = RagResponse.model_json_schema())
                | JsonOutputParser()
        )
        self.final_answer_chain = self.final_answer_prompt | self.llm | StrOutputParser()


    def simple_invoke(self, prompt: str):
        return self.llm.invoke(input=prompt)

    def multi_hop_rag_invoke(self, prompt: str, retriever: BaseRetriever, max_iterations: int = 4):

        decomposed_prompt = self.decompose_chain.invoke({"question": prompt})

        logging.info(f"Decomposed_questions: {decomposed_prompt}")

        answers = []
        context_for_final_answer = []
        supporting_idx = set()
        rag_answer = None

        for i, question in enumerate(decomposed_prompt):
            if i > max_iterations:
                break

            question = question.strip()

            if i > 0:
                retriever_prompt = f"Based on the answer '{rag_answer}', {question}"
            else:
                retriever_prompt = question

            logging.info(f"--- Question: {question}")

            context = retriever.invoke(retriever_prompt)

            rag_answer = self.rag_chain.invoke(
                {
                    "subquestion": question,
                    "context": context,
                    "main_question": prompt,
                    "prev_questions": "\n".join(context_for_final_answer)
                }
            )

            logging.info(f"--- RAG answer: {rag_answer}")

            answer_source = rag_answer['source_id']
            supporting_idx.add(answer_source)
            answer_text = rag_answer['answer']

            if answer_text.upper().find("I DON'T KNOW") != -1:
                continue

            answers.append(answer_text)

            context_for_final_answer.append(f"Question {i}: {question}\nAnswer {i}: {answer_text}")

            logging.info(f"--- Answer: {answer_text}")

        final_answer = self.final_answer_chain.invoke({
            "original_question": prompt,
            "answers": "\n".join(context_for_final_answer)
        })
        return final_answer, list(supporting_idx)


# llm = ChatOllama(model="phi3.5")
