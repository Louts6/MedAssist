import xxhash
import datetime
# from service.core.rag.app.naive  import  chunk
from service.core.rag.app.manual  import  chunk
from service.core.rag.utils.es_conn import ESConnection
from service.core.rag.nlp.model import generate_embedding


def dummy(prog=None, msg=""):
    pass

def parse(file_path):
    # 使用自定义的 PDF 解析器
    result = chunk(file_path, callback=dummy)
    return result



def process_item(item, file_name, session_id):
    """
    处理单条数据
    """
    try:
        # 生成 chunk_id
        chunck_id = xxhash.xxh64((item["content_with_weight"] + session_id).encode("utf-8")).hexdigest()

        # 构建数据字典
        d = {
            "id": chunck_id,
            "content_ltks": item["content_ltks"],
            "content_with_weight": item["content_with_weight"],
            "content_sm_ltks": item["content_sm_ltks"],
            "important_kwd": [],
            "important_tks": [],
            "question_kwd": [],
            "question_tks": [],
            "create_time": str(datetime.datetime.now()).replace("T", " ")[:19],
            "create_timestamp_flt": datetime.datetime.now().timestamp()
        }



        d["kb_id"] = session_id
        d["docnm_kwd"] = item["docnm_kwd"]
        d["title_tks"] = item["title_tks"]
        d["doc_id"] = xxhash.xxh64(file_name.encode("utf-8")).hexdigest()
        d["docnm"] = file_name
        
        v = generate_embedding(item["content_with_weight"])
        
        # 将嵌入向量存储到字典中
        d["q_%d_vec" % len(v)] = v

        return d

    except Exception as e:
        print(f"process_item error: {e}")
        return None

def execute_insert_process(file_path, file_name, session_id):
    """
    执行文档处理和插入 Elasticsearch 的函数
    :param file_path: 文件路径
    :param session_id: 会话 ID
    :param documents: 要插入的文档列表
    """
    documents = parse(file_path)
    result = []
    for item in documents:
        processed_item = process_item(item, file_name, session_id)
        result.append(processed_item)
    
    # 创建 ESConnection 的实例
    es_connection = ESConnection()
    # 通过实例调用 insert 方法
    es_connection.insert(documents=result, indexName=session_id)



import json
import os

if __name__ == "__main__":
    file_path = "/mnt/d/wsl/project/gsk-poc/storage/file/【兴证电子】世运电路2023中报点评.pdf"
    session_id = "40e2743ccffa4207"
    output_file = "/mnt/d/wsl/project/gsk-poc/storage/output/result.json"

    # 如果本地文件不存在，则解析文件并保存结果
    if not os.path.exists(output_file):
        documents = parse(file_path)
        
        # 处理每个文档
        result = []
        for item in documents:
            processed_item = process_item(item, file_path, session_id)
            result.append(processed_item)

        # 将结果保存到本地文件
        os.makedirs(os.path.dirname(output_file), exist_ok=True)  # 确保目录存在
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print(f"结果已保存到本地文件: {output_file}")
    else:
        # 如果本地文件存在，则从文件中读取结果
        with open(output_file, "r", encoding="utf-8") as f:
            result = json.load(f)
        print(f"从本地文件加载结果: {output_file}")

    # # 打印结果以便检查
    # print("加载的数据内容：")
    # print(json.dumps(result, ensure_ascii=False, indent=4))

    # 创建 ESConnection 的实例
    es_connection = ESConnection()
    # 通过实例调用 insert 方法
    es_connection.insert(documents=result, indexName="世运电路2023中报点评")

