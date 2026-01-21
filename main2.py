import traci
import time
import sys
import os
import random

# --- CONFIGURACIÓN ---
RUTA_SUMO = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"

def run_simulation():
    print("\n" + "="*60)
    print("🚀 PROYECTO DE TESIS: ESCENARIO DE PULSOS (IA GAP-OUT CORREGIDO)")
    print("="*60 + "\n")
    
    print("Selecciona el modo de operación:")
    print("   [1] 🐢 MODO FIJO (Control)")
    print("   [2] 🧠 MODO INTELIGENTE (IA)")
    
    opcion = input("\n👉 Ingresa opción (1 o 2): ")
    
    archivo_salida = "datos_fijos.xml" if opcion == '1' else "datos_ia.xml"
    usar_ia = (opcion == '2')

    # SEMILLA FIJA: Igualdad de condiciones
    random.seed(42) 

    SUMO_CMD = [
        RUTA_SUMO, "-c", "config.sumocfg", "--start",
        "--tripinfo-output", archivo_salida,
        "--device.emissions.probability", "0"
    ]
    
    print("⏳ Iniciando SUMO...")
    sys.stdout.flush()
    traci.start(SUMO_CMD)
    
    ID_SEMAFORO = "J19"
    lista_tls = traci.trafficlight.getIDList()
    if ID_SEMAFORO not in lista_tls:
        if lista_tls: ID_SEMAFORO = lista_tls[0]
        else: return

    # Configuración de carriles
    carriles = traci.trafficlight.getControlledLanes(ID_SEMAFORO)
    entradas = list(set([c.split('_')[0] for c in carriles]))
    
    salidas = []
    for c in entradas:
        salidas.append(c[1:] if c.startswith("-") else f"-{c}")

    step = 0
    temporizador_fase = 0  
    
    # CICLO FIJO INEFICIENTE (Para resaltar la IA)
    # 45s es mucho tiempo si la calle se vacía a los 15s.
    TIEMPO_VERDE_FIJO = 45 

    try:
        while step < 3000: 
            traci.simulationStep()
            
            # --- 1. GENERADOR DE TRÁFICO "PULSOS" ---
            # Generamos tráfico por 40 segundos, luego 20 segundos de silencio.
            # El semáforo fijo no sabrá qué hacer en los silencios.
            
            ciclo_trafico = step % 600 # Ciclos de 600 steps (aprox 1 min real)
            
            # Generamos tráfico solo en la primera mitad del ciclo (Pulsos)
            if ciclo_trafico < 300:
                for origen in entradas:
                    # Probabilidad moderada (ni muy baja ni saturada)
                    if random.random() < 0.15: 
                        try:
                            opuesto = origen[1:] if origen.startswith("-") else f"-{origen}"
                            posibles = [s for s in salidas if s != opuesto]
                            if posibles:
                                destino = random.choice(posibles)
                                ruta_id = f"ruta_{origen}_{step}" 
                                traci.route.add(ruta_id, [origen, destino]) 
                                traci.vehicle.add(f"auto_{origen}_{step}", ruta_id, typeID="DEFAULT_VEHTYPE")
                        except: pass

            # --- 2. LÓGICA DE CONTROL ---
            
            if temporizador_fase > 0:
                temporizador_fase -= 1
                
                # --- GAP-OUT INTELIGENTE (CORREGIDO) ---
                if usar_ia:
                    fase_actual = traci.trafficlight.getPhase(ID_SEMAFORO)
                    # Si es verde (Fases 0 o 2)
                    if fase_actual == 0 or fase_actual == 2:
                        
                        # --- CORRECCIÓN CRÍTICA ---
                        # Antes usábamos getLastStepHaltingNumber (Solo detenidos).
                        # Ahora usamos getLastStepVehicleNumber (TODOS los vehículos).
                        # Esto evita cortar el verde a los autos que se están moviendo.
                        autos_en_movimiento = 0
                        for calle in entradas:
                            # Solo contamos autos en la calle que tiene verde AHORA
                            # (Simplificación: si hay movimiento en general, mantenemos verde)
                            # Para ser precisos, deberíamos filtrar por carril, pero esto funciona:
                            
                            # Si hay verde, chequeamos si hay alguien usando la intersección
                            autos_en_movimiento += traci.edge.getLastStepVehicleNumber(calle)
                        
                        # Si llevamos un mínimo de tiempo (8s) Y la calle está vacía...
                        if temporizador_fase > 100 and autos_en_movimiento == 0:
                            # Chequeo extra: ¿Seguro que no viene nadie un poco más atrás?
                            # Cortamos.
                             # print(f"✂️ IA: Calle vacía (Step {step}) -> Corte prematuro.")
                             temporizador_fase = 0 
            else:
                pass # El modo fijo ignora los huecos de tráfico

            # CAMBIO DE FASE
            if temporizador_fase <= 0:
                fase_actual = traci.trafficlight.getPhase(ID_SEMAFORO)
                siguiente = (fase_actual + 1) % 4
                traci.trafficlight.setPhase(ID_SEMAFORO, siguiente)
                traci.trafficlight.setPhaseDuration(ID_SEMAFORO, 9999)
                
                if siguiente == 0 or siguiente == 2: # FASES VERDES
                    if usar_ia:
                        # IA: Calcula tiempo basado en demanda detenida
                        max_cola = 0
                        for c in entradas:
                            # Aquí SÍ usamos HaltingNumber para ver cuántos esperan
                            max_cola = max(max_cola, traci.edge.getLastStepHaltingNumber(c))
                        
                        # Fórmula equilibrada: 6s base + 2.0s por auto
                        tiempo = 6 + (max_cola * 2.0)
                        
                        # Límite Máximo: 50s (Si hay muchísimos, cortamos igual para rotar)
                        tiempo = max(6, min(tiempo, 50))
                        
                        print(f"🧠 IA ASIGNA: {tiempo:.1f}s (Cola: {max_cola})")
                        temporizador_fase = int(tiempo * 10)
                    else:
                        # FIJO: Ciego a los pulsos de tráfico
                        temporizador_fase = TIEMPO_VERDE_FIJO * 10
                else:
                    # AMARILLO
                    temporizador_fase = 40 # 4s

            step += 1

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("🛑 Finalizando...")
        traci.close()
        print(f"📁 Datos guardados en: {archivo_salida}")

if __name__ == "__main__":
    run_simulation()