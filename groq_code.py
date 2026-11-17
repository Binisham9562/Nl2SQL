import os

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine

from llama_index.core import SQLDatabase,settings
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.groq import Groq

from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

app = Flask(__name__)
CORS(app)

from urllib.parse import quote_plus

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name} (set it in .env)")
    return value


DB_DRIVER = os.getenv("DB_DRIVER", "mysql+pymysql")
DB_USER = require_env("DB_USER")
DB_PASS = quote_plus(require_env("DB_PASS"))
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = require_env("DB_NAME")

DATABASE_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

TABLE_FILTER_QUERY = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = DATABASE()
  AND table_type = 'BASE TABLE'
  AND table_name NOT LIKE 'sql_%'
  AND table_name NOT LIKE 'alembic_%'
  AND table_name NOT LIKE 'django_%'
  AND table_name NOT LIKE 'audit_%'
  AND table_name NOT LIKE 'log_%'
  AND table_name NOT LIKE 'tmp_%'
  AND table_name NOT LIKE 'backup_%'
ORDER BY table_name;
"""


engine = create_engine(DATABASE_URL)
# sql_database = SQLDatabase(engine)

from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text(TABLE_FILTER_QUERY))
    ALLOWED_TABLES = [row[0] for row in result]

print(f"📋 Using {len(ALLOWED_TABLES)} application tables")

sql_database = SQLDatabase(
    engine,
    include_tables=ALLOWED_TABLES
)


llm = Groq(
    # model="meta-llama/llama-4-maverick-17b-128e-instruct",
    model="meta-llama/llama-4-scout-17b-16e-instruct" , # or llama3-8b-8192
    api_key=require_env("GROQ_API_KEY"),
    temperature=0
)


query_engine = NLSQLTableQueryEngine(
    sql_database=sql_database,
    llm=llm,
    verbose=True,              # shows generated SQL in console
    synthesize_response=True,
    response_mode="compact"   # returns final natural language answer
)


@app.route("/query", methods=["POST"])
def query_db():
    data = request.get_json()
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "Question is required"}), 400

    # Run LLM -> SQL -> Execute
    response = query_engine.query(user_question)

    return jsonify({
        "question": user_question,
        "answer": str(response),
        "generated_sql": response.metadata.get("sql_query")
    })


if __name__ == "__main__":
    app.run(
        host=os.getenv("APP_HOST"),
        port=int(os.getenv("APP_PORT")),
        debug=os.getenv("APP_DEBUG", "false").lower() == "true",
    )
