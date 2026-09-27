from fastapi import APIRouter, Body, UploadFile, File, HTTPException, Query, status
import uuid
from schemas.chat import ChatRequest
from fastapi.responses import StreamingResponse
import os
from dotenv import load_dotenv
from typing import List
from service.core.file_parse import execute_insert_process
from service.core.api.utils.file_utils import get_project_base_directory
from database.knowledgebase_operations import get_user_history_questions
from service.core.retrieval import retrieve_content
from service.core.chat import get_chat_completion
from service.core.rag.nlp.model import rerank_results
from utils import logger
from typing import List, Optional
from database.knowledgebase_operations import insert_knowledgebase, verify_user_knowledgebase
from service.web_search.procss_web_search import store_and_query_snippets
from service.agent.agent import final_answer
from typing import List
from utils.prompt import DirectAnswerPrompt

# 加载 .env 文件
load_dotenv()

router = APIRouter()



##################################
# 创建一个新的对话 Session
##################################

@router.post("/create_session")
async def create_session(
    # credentials: JwtAuthorizationCredentials = Security(access_security),
):
    try:
        user_id = "1"
        # user_id = credentials.subject.get("user_id")
        # if not user_id:
        #     raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        session_id = str(uuid.uuid4()).replace("-", "")[:16]

        return {
            "session_id": session_id,
            "status": "success",
            "message": "Session created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@router.post("/upload_files/")
async def upload_files(
    session_id: Optional[str] = Query(None),
    files: List[UploadFile] = File(...),
    # credentials: JwtAuthorizationCredentials = Security(access_security),
):
    if session_id is None:
        session_id = "default"  # 设置默认值
    # 确保 storage/file 文件夹存在
    storage_dir = os.path.join(get_project_base_directory(), "storage/file")
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)
    
    # 根据 session_id 创建子文件夹
    session_dir = os.path.join(storage_dir, session_id)
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    try:
        user_id = "1"
        
        for file in files:
            file_name = file.filename
            file_path = os.path.join(session_dir, file_name)
            
            # 保存文件到本地
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())
            
            # 保存文件 URL 和 Base64 编码的文件流
            file_url = f"{storage_dir}/{session_id}/{file_name}"
            # file_streams.append(await file.read())  # 或根据需要处理文件流
            print(file_url)
            print(file_name)

            execute_insert_process(file_url, file_name, user_id)
            logger.info("数据插入es")

            insert_knowledgebase(user_id, file_name)
            logger.info("数据插入pg")

        return {
            "status": "success",
            "message": "文件解析成功"
        }
    
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
##################################
# ai搜索
################################## 

@router.post("/ai_search/")
async def ai_search(
    session_id: str = Query(...),
    request: ChatRequest = Body(..., description="User message"),
    # credentials: JwtAuthorizationCredentials = Security(access_security),
    # db: Session = Depends(get_db),
):
    try:
        user_id = '1'
        
        question = request.message

        
        # 验证用户是否有自己的知识库
        has_knowledgebase = verify_user_knowledgebase(user_id)
        
        knowledgebase_results = []
        if has_knowledgebase:
            # 执行知识库检索
            references = retrieve_content(user_id, question)
            print("知识库查询结果：\n")
            knowledgebase_results = [ref['content_with_weight'] for ref in references]
            print(knowledgebase_results)
        else:
            # 如果用户没有知识库，跳过知识库查询，继续执行其他逻辑
            print("知识库未找到相关查询结果：\n")
            pass

        # 历史上下文
        # 查询 messages 表中对应 session_id 的消息
        history_questions = get_user_history_questions(session_id)

        print("历史问题：\n")
        print(history_questions)


        # 处理web搜索结果
        top_snippets, related_questions = store_and_query_snippets(question)
        web_results = [item["content"] for item in top_snippets]

        final_reference = knowledgebase_results + web_results

        # top_scores, top_texts = rerank_results(question, final_reference)
        # print("重拍后的文本：\n")
        # print(top_texts)
        # formatted_texts = "\n".join([f"{i + 1}. {text}" for i, text in enumerate(top_texts)])
        # print("格式化后的文本：\n")
        # print(formatted_texts)

        # 大模型生成
        final_prompt = DirectAnswerPrompt % (final_reference, history_questions, question)
        
        print(final_prompt)

        # 返回流式响应
        return StreamingResponse(
            get_chat_completion(session_id, question, knowledgebase_results, user_id, final_prompt, related_questions,top_snippets),
            media_type="text/event-stream"
        )

    
    except HTTPException as e:
        # 捕获 HTTPException 并重新抛出，保持状态码和详情
        raise e
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/deep_research/")
async def deep_research(
    session_id: str = Query(...),
    request: ChatRequest = Body(..., description="User message"),
    # credentials: JwtAuthorizationCredentials = Security(access_security),
    # db: Session = Depends(get_db),
):
    try:
        question = request.message
        print("处理问题：")
        print(question)
        # 返回流式响应
        return StreamingResponse(
            final_answer(question),
            media_type="text/event-stream"
        )

    
    except HTTPException as e:
        # 捕获 HTTPException 并重新抛出，保持状态码和详情
        raise e
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
