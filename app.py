
import os
from flask import Flask, request, jsonify
from llama_index.llms.groq import Groq
from llama_index.core.agent import ReActAgent
# from llama_index.core.agent.react import ReActAgent
from llama_index.core.tools import ToolMetadata,FunctionTool
from llama_index.core import SQLDatabase
from llama_index.core.indices.struct_store import NLSQLTableQueryEngine
from sqlalchemy import create_engine
from dotenv import load_dotenv
from system_prompt import AGENT_SYSTEM_PROMPT, TEXT_TO_SQL_PROMPT, RESPONSE_SYNTHESIS_PROMPT



from llama_index.core import Settings

Settings.embed_model = None


import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

load_dotenv()


# ----------------------------------------------------------
# 2. Groq LLM (LlamaIndex)
# ----------------------------------------------------------
def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name} (set it in .env)")
    return value

GROQ_API_KEY = require_env("GROQ_API_KEY")

llm = Groq(
    model=os.getenv("GROQ_MODEL"),
    api_key=GROQ_API_KEY,
    temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
    is_function_calling_model=False,
    max_tokens=int(os.getenv("LLM_MAX_TOKENS", "800"))
)


from urllib.parse import quote_plus

DB_DRIVER = os.getenv("DB_DRIVER", "mysql+pymysql")
DB_USER = require_env("DB_USER")
DB_PASS = quote_plus(require_env("DB_PASS"))  # handles special chars like '@'
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = require_env("DB_NAME")

engine = create_engine(f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
sql_db = SQLDatabase(engine)

# ---------------------------
# 3. SQL Query Engine
# ---------------------------
query_engine = NLSQLTableQueryEngine(
    sql_database=sql_db,
    verbose=True,
    llm=llm,
    text_to_sql_prompt=TEXT_TO_SQL_PROMPT,
    response_synthesis_prompt=RESPONSE_SYNTHESIS_PROMPT,
)

# ---------------------------
# 4. SQL Tool
# ---------------------------
def run_sql_query(input: str) -> str:
    """Run a natural language question against the SQL database and return the answer."""
    return str(query_engine.query(input))

sql_tool = FunctionTool(
    run_sql_query,  # synchronous callable
    metadata=ToolMetadata(
        name="sql_tool",
        description=(
            "Answers questions about the classicmodels database (customers, employees, "
            "offices, orders, orderdetails, products, productlines, payments). "
            "Input must be a complete natural-language question; ask for names "
            "(customer, employee, product, office) rather than IDs. The tool converts "
            "it to SQL, runs it, and returns the answer."
        )
    )
)

# ---------------------------
# 5. Agent
# ---------------------------
agent = ReActAgent(
    llm=llm,
    tools=[sql_tool],
    system_prompt=AGENT_SYSTEM_PROMPT,
    verbose=True,
    max_iterations=5
)

# ---------------------------
# 6. Flask App
# ---------------------------
# app = Flask(__name__)

# @app.route("/", methods=["GET"])
# def home():
#     return "Server is running!"

from quart import Quart, request, jsonify

app = Quart(__name__)
@app.route("/", methods=["GET"])
async def home():
    return "Server is running!"


@app.route("/query", methods=["POST"])
async def query():
    data = await request.get_json()
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "Missing 'question' field"}), 400

    # Synchronous LLM call
    response = await agent.run(user_question) 

    return jsonify({
        "question": user_question,
        "answer": str(response),
    }), 200

if __name__ == "__main__":
    app.run(
        host=os.getenv("APP_HOST"),
        port=int(os.getenv("APP_PORT")),
        debug=os.getenv("APP_DEBUG", "false").lower() == "true",
    )
