import gradio as gr
from langchain.chains import LLMChain, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from vector_store import get_vector_store_global, get_vector_store_temp
from prompt_builder import process_user_query_two_stage, get_summary_measures_prompt

# Vetores globais
vector_store = get_vector_store_global()
retriever_global = vector_store.as_retriever()

# Vetor temporário da FINE
retriever_temporario = None

# Memórias separadas
memory_geral = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
memory_fine = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

def handle_upload(file):
    global retriever_temporario
    if file is None:
        return "⚠️ Nenhum ficheiro carregado."
    try:
        if not file.name.lower().endswith('.pdf'):
            return "❌ Por favor, carrega apenas ficheiros PDF."
        
        retriever_temporario = get_vector_store_temp(file.name)
        return "✅ Documento carregado e pronto para análise!"
    except FileNotFoundError:
        retriever_temporario = None
        return "❌ O ficheiro não foi encontrado. Por favor, tenta novamente."
    except PermissionError:
        retriever_temporario = None
        return "❌ Erro de permissão ao aceder ao ficheiro. Por favor, verifica as permissões."
    except Exception as e:
        retriever_temporario = None
        return f"❌ Ocorreu um erro ao processar o ficheiro: {str(e)}"

def limpar_pdf():
    global retriever_temporario
    retriever_temporario = None
    return "❌ O documento foi eliminado."

def resumir_medidas_governo():
    global vector_store
    all_docs = vector_store.get()["documents"]
    metadados = vector_store.get()["metadatas"]

    # Filtra por ficheiro específico
    chunks_apoios = [
        doc for doc, meta in zip(all_docs, metadados)
        if meta.get("source_file") == "medidas_do_governo.md"
    ]

    if not chunks_apoios:
        return "❌ Não foram encontrados conteúdos do ficheiro 'medidas_do_governo.md'."

    context = "\n".join(chunks_apoios)

    # Gera o resumo com LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    summary_chain = LLMChain(llm=llm, prompt=get_summary_measures_prompt())
    resumo = summary_chain.invoke({"context": context})

    return resumo["text"]

def echo_geral(message, history):
    global retriever_global
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    prompt_template = process_user_query_two_stage(
        user_input=message, 
        vector_store=retriever_global, 
        llm=llm, 
        use_imt_specific="imt" in message.lower()
    )

    if isinstance(prompt_template, str):
        return prompt_template

    conv_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever_global,
        memory=memory_geral,
        combine_docs_chain_kwargs={"prompt": prompt_template},
        return_source_documents=False
    )

    response = conv_chain({"question": message})
    return response["answer"]

def echo_fine(message, history):
    global retriever_temporario

    if not retriever_temporario:
        return "⚠️ Nenhum documento FINE carregado. Por favor, faz upload antes de continuar."

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    # Get the appropriate prompt template
    prompt_template = process_user_query_two_stage(
        user_input=message, 
        vector_store=retriever_temporario, 
        llm=llm
    )

    # If we got a string response (like out of scope), return it directly
    if isinstance(prompt_template, str):
        return prompt_template

    retriever = retriever_temporario.as_retriever()
    conv_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory_fine,
        combine_docs_chain_kwargs={"prompt": prompt_template},
        return_source_documents=False
    )
    response = conv_chain({"question": message})
    return response["answer"]

# Função para limpar memória + chatbot
# def reset_chat_history(memory, chatbot):
#     memory.clear()
#     return []


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🏡 Descomplica o Crédito à Habitação")
    gr.Markdown("👋 Olá! Bem-vindo ao teu assistente de Crédito à Habitação! Em que te posso ajudar?")
    
    with gr.Tabs() as tabs:
        with gr.Tab("💬 Geral"):
            with gr.Row():
                # Coluna do chat (mais larga)
                with gr.Column(scale=8, min_width=500):
                    chatbot_geral = gr.Chatbot(height=650, show_copy_button=True)
                    gr.ChatInterface(fn=echo_geral, type="messages", chatbot=chatbot_geral, save_history=True)
                    # botao_reset_geral = gr.Button("🔄 Reiniciar conversa")
                    # botao_reset_geral.click(
                    #     fn=lambda: reset_chat_history(memory_geral, chatbot_geral),
                    #     outputs=chatbot_geral
                    # )

                # Coluna do resumo (mais estreita)
                with gr.Column(scale=5, min_width=400):
                    gr.Markdown("### ✨ Funcionalidade Extra")
                    gr.Markdown("Aqui tens um pequeno resumo sobre os **Apoios do Governo** atualmente em vigor. Espero que te seja útil!")
                    resumo_button = gr.Button("🔍 Gerar Resumo")
                    resumo_output = gr.Markdown(value="", max_height=500)
                    resumo_button.click(fn=resumir_medidas_governo, outputs=resumo_output)


        with gr.Tab("📄 FINE"):
            gr.Markdown("Carrega o teu documento **FINE** para uma análise personalizada.")
            file_input = gr.File(label="Seleciona o ficheiro PDF:", file_types=[".pdf"])
            
            upload_button = gr.Button("📤 Processar documento")
            upload_output = gr.Markdown()

            # Quando carrega ficheiro e clica no botão
            upload_button.click(fn=handle_upload, inputs=file_input, outputs=upload_output)

            # Quando remove o ficheiro (ação da cruz do gr.File)
            file_input.clear(fn=limpar_pdf, outputs=upload_output)
            
            
            # with gr.Row(equal_height=True):
            #     upload_button = gr.Button("📤 Processar documento")
            #     limpar_button = gr.Button("🗑️ Limpar documento")
            # upload_output = gr.Markdown()

            # upload_button.click(fn=handle_upload, inputs=file_input, outputs=upload_output)
            # limpar_button.click(fn=limpar_pdf, outputs=upload_output)

            chatbot_fine = gr.Chatbot()
            gr.ChatInterface(fn=echo_fine, type="messages", chatbot=chatbot_fine)
            # botao_reset_fine = gr.Button("🔄 Reiniciar conversa")
            # botao_reset_fine.click(
            #     fn=lambda: reset_chat_history(memory_fine, chatbot_fine),
            #     outputs=chatbot_fine
            # )
            
    gr.HTML(
    """
    <div style='background-color:#f5f5f5; padding:10px; border-radius:8px;
                border:1px solid #ddd; text-align:center; font-size:14px; color:#444;'>
        ⚠️ Este projeto destina-se apenas a fins informativos e educacionais, não constituindo aconselhamento financeiro.
        Todas as decisões financeiras são da inteira responsabilidade do utilizador.
    </div>
    """
    )

if __name__ == "__main__":
    demo.launch()