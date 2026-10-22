import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

load_dotenv()

class MockLLM(BaseChatModel):
    """LLM de prueba (Mock) que simula respuestas cuando no hay créditos o claves válidas."""
    

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs) -> ChatResult:
        last_message = messages[-1].content if messages else ""
        
        if "investiga" in last_message.lower() or "mercado" in last_message.lower():
            text = "Análisis de mercado simulado: Crecimiento constante en adopción de orquestadores jerárquicos (2026)."
        elif "analiza" in last_message.lower() or "métricas" in last_message.lower():
            text = "Métricas calculadas: Eficiencia incrementada en +42.5% con margen de error del <2%."
        else:
            text = "Respuesta simulada correctamente por el modo Mock."
            
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    @property
    def _llm_type(self) -> str:
        return "mock"


def get_llm(temperature: float = 0.0):
    """
    Retorna la instancia de Chat Model según LLM_PROVIDER ('openai' o 'groq').
    Sino, cae transparentemente a MockLLM.
    """
    
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    # Opción 1: Provider OpenAI
    if provider == "openai" and openai_api_key:
        try:
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=temperature,
                api_key=openai_api_key,
                max_retries=1 # Evita esperas largas si falla la cuenta
            )
        except Exception as e:
            print(f" Error al inicializar OpenAI ({e}). Usando MockLLM como respaldo.")
            return MockLLM()

    # Opción 2: Provider Groq
    if provider == "groq" and groq_api_key:
        try:
            return ChatGroq(
                model_name="llama-3.3-70b-versatile",
                temperature=temperature,
                groq_api_key=groq_api_key,
                max_retries=1
            )
        except Exception as e:
            print(f" Error al inicializar Groq ({e}). Usando MockLLM como respaldo.")
            return MockLLM()            

    # Opción 3: Si LLM_PROVIDER es 'mock' o faltan las API Keys correspondientes
    print(" Ejecutando en modo 'Mock' (Simulación sin consumo de API).")
    return MockLLM()