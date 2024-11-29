import telebot
import os
os.environ["OPENAI_API_KEY"] = "chave_api_LLM"
from llama_index.core import PromptTemplate
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import StorageContext, load_index_from_storage



bot = telebot.TeleBot('Chave_bot')

documents = SimpleDirectoryReader('./dados').load_data()

TEMPLATE_STR = (
    "Nós fornecemos informações de contexto abaixo.\n"
    "---------------------\n"    
    "Você deverá desempenhar o papel de um vendedora de Sanduiches. O seu nome é tiburcia, você é um Vendedora Digital de sanduiche. Você deverá somente responder as dúvidas dos clientes usando como base o contexto abaixo que contem informações sobre as lanches.\n"
    "{context_str}"
    "\n---------------------\n"    
    "Para comprar bastar acessar"
    "\n---------------------\n"
    "Com base nessas informações, por favor responda à pergunta.: {query_str}\n"
)
QA_TEMPLATE = PromptTemplate(TEMPLATE_STR)

index = VectorStoreIndex.from_documents(documents)

index.storage_context.persist()
storage_context = StorageContext.from_defaults(persist_dir="./storage")

index = load_index_from_storage(storage_context)

query_engine = index.as_query_engine(text_qa_template=QA_TEMPLATE)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Olá! Como posso ajudar você?")


@bot.message_handler(func=lambda message: message.text.lower() in ['adeus', 'tchau', 'até logo', 'bye', 'depois eu volto'])
def goodbye(message):
    bot.send_message(message.chat.id, "Até breve!")


@bot.message_handler(content_types=['text'])
def send_text(message):
    answer = query_engine.query(message.text)
    bot.send_message(message.chat.id, answer)

bot.polling()
