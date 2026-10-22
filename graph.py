from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from state import TeamState
from config import get_llm
from agents.research_agent import research_node
from agents.analyst_agent import analyst_node

# Esquema Pydantic para la salida estructurada del Supervisor
class RouterSchema(BaseModel):
    next_step: Literal["Investigador", "Analista", "FINISH"] = Field(
        description="El próximo agente que debe actuar o FINISH si la tarea está completada con ambos aportes."
    )
    reasoning: str = Field(description="Explicación breve de por qué se toma esta decisión.")

def supervisor_node(state: TeamState) -> dict:
    """Nodo Supervisor: Determina la ruta del flujo basándose en el estado actual y un límite de pasos."""
    step_count = state.get("step_count", 0)
    
    #  Prevención de "Supervisor Infinito"
    if step_count >= 5:
        print(" [Supervisor]: Límite de pasos alcanzado. Finalizando ejecución.")
        return {"next_agent": "FINISH"}
    has_research = bool(state.get("research_data"))
    has_analysis = bool(state.get("analysis_data"))
    
    # Intentamos la decisión mediante el LLM con Structured Output
    try:
        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(RouterSchema)

        system_prompt = (
            "Eres el Supervisor de un equipo jerárquico multi-agente.\n"
            "Tu tarea es evaluar la situación y derivar al especialista adecuado:\n"
            "- Si falta la investigación de mercado, deriva a 'Investigador'.\n"
            "- Si ya existe la investigación pero falta el análisis numérico, deriva a 'Analista'.\n"
            "- Si ambos agentes completaron sus entregables, deriva a 'FINISH'."
        )

        user_content = (
            f"Estado actual:\n"
            f"- Datos de investigación: {'COMPLETADO' if has_research else 'PENDIENTE'}\n"
            f"- Datos de análisis: {'COMPLETADO' if has_analysis else 'PENDIENTE'}\n"
            f"- Pasos ejecutados: {step_count}\n"
            f"Decide el siguiente paso."
        )
        response = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ])
        
        # Si el LLM devolvió un esquema Pydantic válido
        next_step = response.next_step
        
    except Exception as e:
        # Fallback determinista si el LLM/MockLLM no soporta structured output o falla la llamada
        print(f" [Supervisor] Usando lógica determinista de respaldo ({e})")    

        if not has_research:
            next_step = "Investigador"
        elif not has_analysis:
            next_step = "Analista"
        else:
            next_step = "FINISH"

    return {"next_agent": next_step}


def route_decision(state: TeamState) -> str:
    """Función de arista condicional que lee el próximo agente en el estado."""
    return state.get("next_agent", "FINISH")


def build_graph() -> StateGraph:
    """Construye y compila el grafo jerárquico."""
    builder = StateGraph(TeamState)

    # 1. Agregar Nodos
    builder.add_node("Supervisor", supervisor_node)
    builder.add_node("Investigador", research_node)
    builder.add_node("Analista", analyst_node)

    # 2. Definir Punto de Entrada
    builder.set_entry_point("Supervisor")

    # 3. Aristas Condicionales desde el Supervisor
    builder.add_conditional_edges(
        "Supervisor",
        route_decision,
        {
            "Investigador": "Investigador",
            "Analista": "Analista",
            "FINISH": END
        }
    )

    # 4. Retorno de los especialistas al Supervisor
    builder.add_edge("Investigador", "Supervisor")
    builder.add_edge("Analista", "Supervisor")

    return builder.compile()
  
# Exposición de la instancia lista para usar
graph = build_graph()