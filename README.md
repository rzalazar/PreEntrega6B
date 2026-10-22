# Pre-entrega 6: Orquestador Multi-Agente Jerárquico de Análisis e Investigación

Proyecto correspondiente a la **Pre-entrega 6** del curso de IA / Agentes de Coderhouse. Consiste en la implementación de un prototipo funcional de un **Orquestador Multi-Agente Jerárquico** desarrollado con **LangGraph**, **LangChain**, **Pydantic** y soporte multiproveedor (**OpenAI**, **Groq** y **MockLLM**).

---

## Consigna y Requerimientos de la Entrega

### Objetivo
Desarrollar un **Orquestador Multi-Agente de Análisis e Investigación**. El sistema de orquestación debe ser capaz de procesar solicitudes complejas requeridas por el usuario que involucren al menos dos dominios de especialización y una fase de síntesis o validación final.

### Requerimientos Técnicos Cumplidos
1. **Topología Jerárquica:** Un nodo **Supervisor** central que actúa como router inteligente y controlador del flujo de trabajo.
2. **Especialistas ReAct con Herramientas:**
   - **Agente de Búsqueda/Investigación (`research_agent.py`):** Consulta de mercado mediante herramientas customizadas de búsqueda con coincidencia flexible.
   - **Agente de Análisis/Cómputo (`analyst_agent.py`):** Procesamiento cuantitativo y cálculo de métricas de rendimiento con manejo de excepciones.
3. **Estado Compartido Estructurado (`state.py`):** Esquema `TeamState` basado en `TypedDict` con `add_messages`, almacenamiento de entregables (`research_data`, `analysis_data`) y contador de iteraciones (`step_count`).
4. **Flujo de Supervisión y Salida Estructurada:** Uso de `RouterSchema` con `with_structured_output` (y respaldo determinista) para validar la suficiencia de los datos antes de emitir la transición hacia `FINISH`.
5. **Demostración Práctica:** Notebook ejecutable (`demo.ipynb`) y script asíncrono (`main.py`) para validar el streaming de estados y delegación paso a paso.

---

## Diagrama Mermaid del Grafo

```mermaid
graph TD
    START([Inicio]) --> Supervisor
    
    Supervisor -->|Decisión: Investigador| Investigador
    Supervisor -->|Decisión: Analista| Analista
    Supervisor -->|Decisión: FINISH| END([Fin])
    
    Investigador -->|Retorno con datos| Supervisor
    Analista -->|Retorno con análisis| Supervisor
```

![Diagrama del Grafo Jerárquico](./graph_diagram.png)

---

## Justificación de la Topología Elegida

Se seleccionó una **Topología Jerárquica (Hub-and-Spoke / Supervisor-Workers)** por los siguientes motivos de arquitectura de software:

1. **Desacoplamiento y Especialización Estricta (SRP):**  
   Cada agente especialista (`Investigador` y `Analista`) opera como una unidad con responsabilidad única. El investigador se enfoca exclusivamente en consumir herramientas externas y recolectar información, mientras que el analista procesa cuantitativamente esa información sin preocuparse por la fase de recolección.
2. **Control Centralizado y Rúbrica de Validación:**  
   Al hacer que todas las aristas de retorno pasen obligatoriamente por el **Supervisor**, nos aseguramos de que exista un nodo de validación en cada iteración. El supervisor evalúa si se han completado los requerimientos de la consigna antes de dar por finalizada la tarea (`FINISH`).
3. **Escalabilidad del Sistema:**  
   Esta topología permite agregar nuevos agentes especialistas (por ejemplo, un *Agente Redactor* o un *Agente de Control de Calidad*) añadiendo únicamente el nodo correspondiente al grafo y la opción en el `Literal` de la salida estructurada del Supervisor, sin modificar la lógica interna de los demás nodos.

---

## Manejo de Conflictos y Prevención de Bucles

Para cumplir con los estándares de resiliencia y evitar errores comunes en sistemas multi-agente, se implementaron dos estrategias principales:

### 1. Prevención del "Supervisor Infinito" (Bucles Eternos)
- **Contador de Pasos (`step_count`):** El estado compartido `TeamState` mantiene un contador de iteraciones. Si el grafo alcanza un límite estricto de ejecuciones (`step_count >= 5`), el Supervisor fuerza la salida hacia `FINISH` independientemente de la respuesta del modelo, evitando costos excesivos en la API o bloqueos infinitos.
- **Criterio de Suficiencia Estricto:** El Supervisor valida explícitamente la presencia de los campos `research_data` y `analysis_data`. Si ambos entregables están cargados, la decisión conmuta a `FINISH` inmediatamente.

### 2. Aislamiento de Estado y Contaminación de Contexto
- En lugar de saturar el ventana de contexto enviando todo el historial de conversaciones e imágenes de metadatos a cada especialista, se utilizan campos dedicados en `TeamState`.
- Cada agente recibe solo el artefacto o instrucción específica que necesita para ejecutar su herramienta, reduciendo la latencia de inferencia y aumentando la precisión en las respuestas (*context clutter reduction*).