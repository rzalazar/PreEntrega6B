import asyncio
from langchain_core.messages import HumanMessage
from graph import graph


async def run_demo():
    # Intenta generar el diagrama visual del grafo si Mermaid está disponible
    try:
        with open("graph_diagram.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Diagrama 'graph_diagram.png' actualizado.")
    except Exception:
        pass  # Si no hay conexión o falla, continúa la ejecución normalmente

    query = (
        "Necesito investigar la adopción de LangGraph en el mercado "
        "y calcular las métricas de rendimiento proyectadas."
    )

    print("\n" + "=" * 80)
    print("INICIANDO ORQUESTADOR MULTI-AGENTE JERÁRQUICO")
    print(f"Solicitud: {query}")
    print("=" * 80 + "\n")

    initial_state = {
        "messages": [HumanMessage(content=query)],
        "next_agent": "Supervisor",
        "research_data": None,
        "analysis_data": None,
        "step_count": 0,
    }

    # Ejecución asíncrona por pasos (astream)
    async for output in graph.astream(initial_state):
        for node_name, state_update in output.items():
            print(f"[NODO EJECUTADO]: {node_name}")
            if "next_agent" in state_update:
                print(
                    f"   -> Decisión del Supervisor: Ir a '{state_update['next_agent']}'"
                )
            if "messages" in state_update:
                print(f"   Mensaje: {state_update['messages'][-1].content}\n")

    print("=" * 80)
    print("FLUJO FINALIZADO CON ÉXITO")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_demo())