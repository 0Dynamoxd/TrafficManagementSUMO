import traci
import time
import sys
import os
import random

# --- CONFIGURACIÓN ---
RUTA_SUMO = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
# Usamos --start para que arranque solo
SUMO_CMD = [RUTA_SUMO, "-c", "config.sumocfg", "--start"]

def run_smart_road():
    print("\n" + "="*60)
    print("🚀 PROYECTO DE TESIS: CONTROL ADAPTATIVO")
    print("📊 MODO: VISUALIZACIÓN DE DATOS EN TIEMPO REAL")
    print("="*60 + "\n")
    
    print("⏳ Conectando con SUMO...")
    sys.stdout.flush() # Fuerza a imprimir en consola
    
    traci.start(SUMO_CMD)
    print("✅ ¡Simulación Iniciada! Recopilando datos...")
    
    ID_SEMAFORO = "J19"
    
    # 1. Validación
    lista_tls = traci.trafficlight.getIDList()
    if ID_SEMAFORO not in lista_tls:
        if lista_tls: ID_SEMAFORO = lista_tls[0]
        else: return

    # 2. Configuración de calles
    carriles_entrantes = traci.trafficlight.getControlledLanes(ID_SEMAFORO)
    entradas = list(set([c.split('_')[0] for c in carriles_entrantes]))
    
    salidas = []
    for calle in entradas:
        if calle.startswith("-"): salidas.append(calle[1:]) 
        else: salidas.append(f"-{calle}")
    
    step = 0
    temporizador_fase = 0  
    
    while step < 10000: 
        traci.simulationStep()
        
        # --- A. GENERADOR DE TRÁFICO (Hora Pico) ---
        if step % 6 == 0:  
            for origen in entradas:
                if random.random() < 0.6: 
                    try:
                        if origen.startswith("-"): opuesto = origen[1:]
                        else: opuesto = f"-{origen}"
                        posibles = [s for s in salidas if s != opuesto]
                        if posibles:
                            destino = random.choice(posibles)
                            ruta_id = f"ruta_{origen}_{step}" 
                            traci.route.add(ruta_id, [origen, destino]) 
                            traci.vehicle.add(f"auto_{origen}_{step}", ruta_id, typeID="DEFAULT_VEHTYPE")
                    except: pass 

        # --- B. SENSADO DE COLAS ---
        max_cola_individual = 0
        total_esperando = 0
        reporte_colas = {} 

        for calle in entradas:
            try:
                cola = traci.edge.getLastStepHaltingNumber(calle)
                total_esperando += cola
                reporte_colas[calle] = cola
                if cola > max_cola_individual:
                    max_cola_individual = cola
            except: pass

        # --- C. REPORTE EN TIEMPO REAL (LO QUE FALTABA) ---
        # Imprimimos el estado CADA SEGUNDO (cada 10 pasos)
        # para que veas que el sistema está leyendo los autos.
        if step % 10 == 0:
            fase_actual = traci.trafficlight.getPhase(ID_SEMAFORO)
            color = "VERDE" if (fase_actual == 0 or fase_actual == 2) else "AMARILLO/ROJO"
            tiempo_restante = int(temporizador_fase / 10)
            
            # Esto imprimirá una línea que se actualiza constantemente
            print(f"👀 MONITOREO | Fase: {fase_actual} ({color}) | Autos Totales: {total_esperando} | Cambio en: {tiempo_restante}s")
            sys.stdout.flush() # Importante para PowerShell

        # --- D. ALGORITMO INTELIGENTE ---
        if temporizador_fase > 0:
            temporizador_fase -= 1
        else:
            # === MOMENTO DE DECISIÓN ===
            print("\n" + "▒"*60)
            print("🧠 CEREBRO ACTIVADO: CALCULANDO NUEVOS TIEMPOS...")
            
            fase_antigua = traci.trafficlight.getPhase(ID_SEMAFORO)
            nueva_fase = (fase_antigua + 1) % 4
            
            # Cambiar fase y bloquear
            traci.trafficlight.setPhase(ID_SEMAFORO, nueva_fase)
            traci.trafficlight.setPhaseDuration(ID_SEMAFORO, 1000)
            
            tiempo_base = 10 
            
            # Si es VERDE (Fases 0 o 2)
            if nueva_fase == 0 or nueva_fase == 2:
                tiempo_extra = max_cola_individual * 4 
                tiempo_total = min(tiempo_base + tiempo_extra, 90)
                
                print(f"🚦 NUEVA LUZ VERDE (Fase {nueva_fase})")
                print(f"   📊 AUTOS DETECTADOS POR CALLE: {reporte_colas}")
                if max_cola_individual > 0:
                    print(f"   ⚠️ Calle crítica tiene {max_cola_individual} autos.")
                    print(f"   🧮 FÓRMULA: 10s base + ({max_cola_individual} * 4s)")
                else:
                    print(f"   🍃 Tráfico libre.")
                
                print(f"   ✅ TIEMPO FINAL ASIGNADO: {tiempo_total} SEGUNDOS")
                temporizador_fase = tiempo_total * 10
            
            else:
                # AMARILLO
                print(f"⚠️ CAMBIO A AMARILLO (Transición)")
                temporizador_fase = 40 # 4 segundos
            
            print("▒"*60 + "\n")

        step += 1
        time.sleep(0.1) 

    traci.close()

if __name__ == "__main__":
    run_smart_road()