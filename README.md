# TrafficManagementSUMO
# Simulación de Control de Tráfico Urbano con SUMO & TraCI

![Estado del Proyecto](https://img.shields.io/badge/Estado-Finalizado-green)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![SUMO](https://img.shields.io/badge/Simulator-SUMO-orange)

##  Descripción

Este repositorio contiene la implementación de una simulación de tráfico vehicular utilizando **SUMO (Simulation of Urban MObility)**. El objetivo principal del proyecto es controlar la lógica de los semáforos en una intersección urbana mediante scripts externos desarrollados en **Python**, utilizando la interfaz **TraCI (Traffic Control Interface)**.

Este proyecto sirve como prototipo de validación lógica para sistemas de gestión de tráfico inteligente, permitiendo probar algoritmos de flujo vehicular en un entorno virtual seguro antes de su implementación física.

##  Características Principales

* **Diseño de Red Vial:** Creación de nodos, aristas y conexiones utilizando *Netedit*.
* **Generación de Demanda:** Configuración de rutas (`.rou.xml`) y flujos vehiculares dinámicos.
* **Control en Tiempo Real:** Uso de la librería `traci` para manipular las fases de los semáforos desde Python durante la ejecución.
* **Recolección de Datos:** Monitoreo de tiempos de espera y longitud de colas simuladas.

##  Tecnologías Utilizadas

* **[SUMO (Simulation of Urban MObility)](https://eclipse.dev/sumo/):** Simulador de tráfico microscópico de código abierto.
* **Python:** Lenguaje de programación para la lógica de control.
* **TraCI:** API para conectar Python con el núcleo de simulación de SUMO.
* **XML:** Formato para la definición de redes y rutas.

##  Requisitos Previos

Para ejecutar este proyecto necesitas tener instalado:

1.  **Python 3.8+**
2.  **SUMO Simulator** (y asegurarte de que la variable de entorno `SUMO_HOME` esté configurada).
3.  Librerías de Python necesarias:
    ```bash
    pip install traci
    pip install eclipse-sumo
    ```

##  Estructura del Proyecto

```text
├── configuration.sumocfg   # Archivo de configuración principal de SUMO
├── network.net.xml         # Definición de la red vial (mapa)
├── routes.rou.xml          # Definición de vehículos y rutas
├── main.py                 # Script de Python con la lógica de control (TraCI)
└── README.md               # Documentación del proyecto
