import telebot
import os
import requests
from llama_index.core import PromptTemplate, VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage

# Configurações
TELEGRAM_API_KEY = '6848456240:AAF9PvYwRWxYnwl8GdRkqDeBxQ5Hr0_-Mo8'
ASSEMBLYAI_API_KEY = '5c90d108ca6845439de96e0f6ab9c649'

bot = telebot.TeleBot(TELEGRAM_API_KEY)

documents = SimpleDirectoryReader('./dados').load_data()
TEMPLATE_STR = (
    "Nós fornecemos informações de contexto abaixo.\n"
    "---------------------\n"    
    "Você deverá desempenhar o papel de um vendedor de peças veículares. O seu nome é Cecilia, você é um Vendedor Digital. Você deverá somente responder as dúvidas dos clientes usando como base o contexto abaixo que contém informações sobre as peças veículares da loja.\n"
    "{context_str}"
    "\n---------------------\n"    
    "Para comprar bastar acessar"
    "\n---------------------\n"
    "Com base nessas informações, por favor responda à pergunta: {query_str}\n"
)
QA_TEMPLATE = PromptTemplate(TEMPLATE_STR)
index = VectorStoreIndex.from_documents(documents)
index.storage_context.persist()
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
query_engine = index.as_query_engine(text_qa_template=QA_TEMPLATE)

# Função para transcrever áudio usando AssemblyAI
def transcribe_audio(file_path):
    headers = {
        'authorization': ASSEMBLYAI_API_KEY,
        'content-type': 'application/json'
    }

    # Subir o arquivo para o AssemblyAI
    upload_response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, files={'file': open(file_path, 'rb')})
    audio_url = upload_response.json()['upload_url']

    # Enviar requisição de transcrição
    transcribe_response = requests.post('https://api.assemblyai.com/v2/transcript', headers=headers, json={'audio_url': audio_url})
    transcript_id = transcribe_response.json()['id']

    # Obter transcrição
    while True:
        result = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers).json()
        if result['status'] == 'completed':
            return result['text']
        elif result['status'] == 'failed':
            return "A transcrição falhou. Por favor, tente novamente."

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

@bot.message_handler(content_types=['voice'])
def handle_audio(message):
    file_info = bot.get_file(message.voice.file_id)
    file_path = bot.download_file(file_info.file_path)
    file_name = "audio.ogg"
    
    with open(file_name, 'wb') as f:
        f.write(file_path)

    transcription = transcribe_audio(file_name)
    os.remove(file_name)

    answer = query_engine.query(transcription)
    bot.send_message(message.chat.id, answer)

bot.polling()
