
from transformers import AutoTokenizer
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler

tokenizer = AutoTokenizer.from_pretrained("gpt2")
token_counter = TokenCountingHandler(tokenizer=tokenizer.encode)
callback_manager = CallbackManager([token_counter])