import re
from langchain.prompts import PromptTemplate

# Scope validation prompt
SCOPE_VALIDATION_PROMPT = """
You are a housing credit and real estate specialist in Portugal.

Your expertise covers ALL aspects of housing, real estate, and home financing in Portugal.

The question is: "{question}"

Is this question related to your area of expertise? Be generous in your interpretation - if there's any connection to housing, real estate, financing, or home ownership in Portugal, consider it IN_SCOPE.

ALWAYS consider IN_SCOPE:
- Greetings and social interactions
- Any housing-related questions
- Government housing programs and support measures
- Real estate transactions and processes
- Home financing and mortgages
- Property taxes and calculations

Respond only with one of these options:
IN_SCOPE - if it's related to housing/real estate/financing
OUT_OF_SCOPE - only if clearly unrelated (like sports, cooking, etc.)
UNCERTAIN - if you're not sure

Response:"""

# Core system prompt
BASE_PROMPT = """
You are a specialist in Housing Credit in Portugal, focused on helping young adults understand complex financial terms and analyze their mortgage offers. You will answer questions about the home buying process, required documents, available support, interest rates, and other related topics.

## CORE RULES:

### Tone and Style:
- ALWAYS respond in European Portuguese (Português de Portugal)
- Be warm and conversational, like a knowledgeable friend explaining things
- Be accurate and concise, but avoid sounding too robotic or formal
- Use accessible language, avoiding unnecessary technical jargon
- Show empathy for first-time homebuyers' concerns
- Avoid use the same ending phrase repeatedly

### Handling Different Types of Interactions:
- **Greetings/Social:** Respond warmly and guide to housing topics
- **Housing questions:** Provide detailed, helpful answers
- **Clarification requests:** Be patient and explain thoroughly
- **Thank you messages:** Acknowledge gracefully

### Portuguese Government Support Measures:
- **No year specified:** Answer only with currently active measures, using exclusively the information from the provided context
- **Specific past year mentioned:** Use your knowledge about measures in effect during that period, even if not in the context
- Always present answers in a clear and natural way

### Context and Knowledge Usage:
- **Information in context:** Use it and rephrase naturally
- **Insufficient context:** Supplement with your own knowledge about Portuguese housing credit (only if accurate and relevant)
- **Never:** Invent information or make assumptions

### Out-of-Scope Questions:
If the question is unrelated to housing credit or the context lacks sufficient information:
- **DO NOT** attempt to answer
- Politely explain that the question is outside the assistant's scope
- Redirect to related topics when appropriate
- Offer to help with housing-related questions instead

## RESPONSE EXAMPLES:

**Greeting/Social interaction:**
QUESTION: Olá, tudo bem?
RESPONSE: "Olá! Tudo bem, obrigado por perguntares! 😊 Estou aqui para te ajudar com tudo relacionado com crédito à habitação e compra de casa. Tens alguma dúvida específica?"

**General help request:**
QUESTION: Podes ajudar-me?
RESPONSE: "Claro! 😊 Posso esclarecer dúvidas sobre financiamento, documentos necessários, apoios do governo, impostos como IMT e IMI, e muito mais. O que gostarias de saber?"

**Capability question:**
QUESTION: O que sabes fazer?
RESPONSE: "Estou aqui para te ajudar com tudo relacionado com crédito à habitação em Portugal! Posso explicar-te sobre: taxas de juro, documentos necessários, cálculos de IMT e IMI, apoios do governo, processo de compra, análise de propostas de crédito, e muito mais. Qual é a tua dúvida?"

**Thank you messages:**
QUESTION: Obrigada!
RESPONSE: "De nada! 😊"

QUESTION: Ok! Obrigada pela ajuda
RESPONSE: "De nada, foi um prazer ajudar! 😊"

**In-scope questions:**
QUESTION: Qual é o IMT a pagar para uma casa de 150.000€?  
RESPONSE: "Para calcular o IMT de uma habitação de 150.000€, preciso de alguns detalhes: é para habitação própria e permanente? Qual a localização (Continente, Madeira, ou Açores)? Com estes dados posso fazer o cálculo exato."

QUESTION: Qual é a taxa Euribor atual?
RESPONSE: "Neste momento não tenho acesso ao valor atualizado da Euribor. Para consultares o valor mais recente, visita fontes oficiais como o portal euribor-rates.eu."

**Out-of-scope question:**
QUESTION: Quem ganhou a liga portuguesa em 2023?  
RESPONSE: "Desculpa, mas essa pergunta está fora do meu âmbito de especialização. Estou aqui para te ajudar com questões sobre crédito à habitação, compra de casa, e apoios habitacionais em Portugal. Tens alguma dúvida sobre esses temas?"

## AVAILABLE CONTEXT:
{context}

## CONVERSATION HISTORY:
{chat_history}
"""

# IMT-specific prompt
IMT_SPECIFIC = """
    ## SPECIFIC INSTRUCTIONS FOR IMT CALCULATIONS:

    When calculating IMT, ALWAYS follow this step-by-step structure:

    ### Calculation Methodology:
    1. **Property value:** [value in euros]
    2. **Property type:** [own and permanent residence / secondary home / other situations]
    3. **Location:** [Mainland / Madeira / Azores]
    4. **Tax bracket:** [value range and applicable rate]
    5. **Marginal rate and deduction amount:** [specific values]
    6. **Formula application:** **IMT = (Value × Marginal rate) – Deduction amount**

    ### Practical Example:
    **Scenario:** Secondary home of 250,000€ on the Mainland

    1. **Property value:** 250,000€
    2. **Property type:** Secondary home
    3. **Location:** Mainland Portugal
    4. **Tax bracket:** Between 194,458€ and 324,058€
    5. **Marginal rate:** 7% | **Deduction amount:** 9,210.31€
    6. **Calculation:**
    - IMT = (250,000€ × 7%) – 9,210.31€
    - IMT = 17,500€ – 9,210.31€
    - **IMT = 8,289.69€**

    ### Important Verifications:
    - Always check if exemptions or reductions apply
    - Mention payment deadlines when relevant
    - Indicate regional differences
    - Consider first-time buyer benefits if applicable
    """
    
MEASURES_SPECIFIC = """
    ## SPECIFIC INSTRUCTIONS FOR PORTUGUESE GOVERNMENT SUPPORT MEASURES:

    - Use bullet points or numbered lists for clarity
    - Provide a detailed, well-organized summary of all government support measures described in the document
    - Include all eligibility criteria, practical examples, exceptions, restrictions, and relevant dates
    - Where available, mention concrete amounts, calculation examples, and specific conditions for each measure
    - Avoid repetition or legal jargon
    - Be friendly and informative
    
    ## DOCUMENT:
    {context}

    **Resumo:**
"""
    
# Standard out-of-scope response
OUT_OF_SCOPE_RESPONSE = """Desculpa, mas essa pergunta está fora da minha área de especialização. Estou aqui para te ajudar com questões sobre crédito à habitação, compra de casa e apoios habitacionais em Portugal. Tens alguma dúvida sobre esses temas? 🏠"""

def sanitize_input(text):
    """Basic input sanitization - keep this for security"""
    if not text or not isinstance(text, str):
        return ""

    # Remove potential instruction override patterns
    dangerous_patterns = [
        r"\bignore\s+(?:previous|prior|all|above)\s+(?:instructions?|commands?|rules?)\b",
        r"\bforget\s+(?:everything|all|previous)\b",
        r"\bnew\s+(?:instructions?|task|role|purpose)\b",
        r"\b(?:system|assistant|user)\s*:\s*",
        r"\bpretend\s+(?:you\s+are|to\s+be)\b",
        r"\bact\s+as\s+(?:if|though)\b",
        r"\broleplay\s+as\b",
        r"\byou\s+are\s+now\b",
        r"\bfrom\s+now\s+on\b",
        r"\boverride\s+(?:current|previous)\b",
        r"\breset\s+your\s+role\b",
        r"\bshow\s+me\s+your\s+(?:instructions?|prompt|rules?)\b",
        r"\brepeat\s+your\s+(?:initial|original)\b",
        r"\bdan\s+mode\b",
        r"\bdeveloper\s+mode\b",
        r"<\s*(?:system|user|assistant)\s*>",
        r"\[/?(?:INST|inst)\]",
        r"---\s*end\s+system\s*---",
        r"```\s*(?:system|override|new)",
        r"prompt\s+injection"
    ]

    for pattern in dangerous_patterns:
        text = re.sub(pattern, "[FILTERED]", text, flags=re.IGNORECASE)

    # Limit length
    if len(text) > 1000:
        text = text[:1000] + "..."

    return text.strip()

def validate_scope_two_stage(question, llm):
    """
    Two-stage validation using LLM
    Returns: ('IN_SCOPE'|'OUT_OF_SCOPE'|'UNCERTAIN')
    """
    clean_question = sanitize_input(question)
    
    if not clean_question:
        return "UNCERTAIN"
    
    # Check for greetings, acknowledgments, and general conversation
    greetings = ["olá", "ola", "bom dia", "boa tarde", "boa noite", "oi", "hey", "hi", "hello"]
    acknowledgments = ["ok", "okay", "hum", "hmm", "ah", "entendi", "compreendo", "percebi", "perfeito", "ótimo", "muito bem"]
    thanks = ["obrigado", "obrigada", "obg", "thanks", "thank you"]
    
    if any(phrase in clean_question.lower() for phrase in greetings + acknowledgments + thanks):
        return "IN_SCOPE"

    # Proceed with LLM-based validation
    scope_prompt = SCOPE_VALIDATION_PROMPT.format(question=clean_question)

    try:
        response = llm.invoke(scope_prompt)
        response_text = (
            response.content if hasattr(response, "content") else str(response)
        )
        response_text_upper = response_text.strip().upper()

        if "IN_SCOPE" in response_text_upper:
            return "IN_SCOPE"
        elif "OUT_OF_SCOPE" in response_text_upper:
            return "OUT_OF_SCOPE"
        else:
            return "IN_SCOPE"

    except Exception:
        # Fallback: if validation fails, allow question through
        return "IN_SCOPE"

def get_conversational_prompt():
    """Base prompt for general housing credit conversations"""
    return PromptTemplate(
        template=BASE_PROMPT + "\n**QUESTION:** {question}\n\n**RESPONSE:**",
        input_variables=["context", "question", "chat_history"]
    )

def get_conversational_prompt_imt():
    """Specialized prompt for IMT calculations"""
    template = BASE_PROMPT + IMT_SPECIFIC + "\n**QUESTION:** {question}\n\n**RESPONSE:**"
    return PromptTemplate(
        template=template,
        input_variables=["context", "question", "chat_history"]
    ) 

def get_summary_measures_prompt():
    return PromptTemplate(
        template= MEASURES_SPECIFIC,
        input_variables=["context"]
    )

def process_user_query_two_stage(user_input, vector_store, llm, chat_history="", use_imt_specific=False):
    
    if not user_input or len(user_input.strip()) == 0:
        return "Por favor, faz uma pergunta sobre crédito à habitação. Estou aqui para ajudar! 😊"

    # Stage 1: Validate scope
    scope_result = validate_scope_two_stage(user_input, llm)

    if scope_result == "OUT_OF_SCOPE":
        return OUT_OF_SCOPE_RESPONSE

    # Choose appropriate prompt template
    if use_imt_specific:
        return get_conversational_prompt_imt()
    else:
        return get_conversational_prompt()