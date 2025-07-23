import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from juego_ia import buscar_jugada, inicializar_tablero, revisar_ganador, reiniciar_indice, indice_actual

app = Flask(__name__)

# Clave secreta necesaria para usar sesiones
app.secret_key = os.urandom(24)

# Estado global
tablero = inicializar_tablero()
turno_actual = "x"
turno_numero = 1
historial = []

### RUTAS PRINCIPALES ###

@app.route("/")
def index():
    tablero_vacio = [["" for _ in range(3)] for _ in range(3)]
    return render_template("index.html", tablero=tablero_vacio)

@app.route("/contador_partidas", methods=["GET"])
def contador_partidas():
    return jsonify({"partidas": indice_actual})

@app.route("/estado", methods=["GET"])
def estado():
    return jsonify({"tablero": tablero, "turno": turno_actual})

@app.route("/info_jugada_sesion", methods=["GET"])
def info_jugada_sesion():
    jugador = session.get("turno_actual", "desconocido").upper()
    modelo = session.get("modelo", "desconocido")
    movimiento = session.get("movimiento", [])

    # if (isinstance(movimiento, list) and len(movimiento) >= 3 and
    #     str(movimiento[0]).lower() == "mark"):
    #     movimiento_texto = f"Mark [{movimiento[1]},{movimiento[2]}]"
    # else:
    #     movimiento_texto = str(movimiento)

    return jsonify({
        "jugador": jugador,
        "modelo": modelo,
        "movimiento": movimiento
    })

@app.route("/reiniciar", methods=["POST"])
def reiniciar():
    global tablero, turno_actual, turno_numero, historial
    tablero = inicializar_tablero()
    turno_actual = "x"
    turno_numero = 1
    historial = []
    reiniciar_indice()
    return jsonify({"estado": "reiniciado"})

@app.route("/jugar_turno", methods=["POST"])
def jugar_turno():
    global tablero, turno_actual, turno_numero, historial

    movimiento, razon, modelo = buscar_jugada(tablero, turno_actual)
    try:
        fila = int(movimiento[1]) - 1
        col = int(movimiento[2]) - 1
    except (IndexError, ValueError):
        return jsonify({"error": "Movimiento inválido.", "tablero": tablero})

    if not (0 <= fila < 3 and 0 <= col < 3):
        return jsonify({"error": "Coordenadas fuera de rango.", "tablero": tablero})

    if tablero[fila][col] == "b":
        tablero[fila][col] = turno_actual
        ganador = revisar_ganador(tablero)

        jugada = {
            "jugador": turno_actual,
            "movimiento": movimiento,
            "razon": razon,
            "modelo": modelo,
            "ganador": ganador,
            "tablero": [row[:] for row in tablero],
            "evaluada": False,
            "match_id": turno_numero
        }
        jugada["evaluacion"] = evaluar_jugada_rubrica(jugada)

        historial.append(jugada)
        guardar_jugada_en_archivo(jugada)

        jugadas = cargar_jugadas_desde_archivo()
        jugadas.append(jugada)
        guardar_jugadas_en_archivo(jugadas)

        #Guardar en evaluaciones.json
        # with open("evaluaciones.json", "a", encoding="utf-8") as f:
        #     f.write(json.dumps(jugada, ensure_ascii=False) + "\n")

        # Actualizar sesión con el nuevo estado
        session["tablero"] = tablero
        session["turno_actual"] = turno_actual
        session["movimiento"] = movimiento
        session["razon"] = razon
        session["modelo"]  =modelo

        
        guardar_imagen_tablero(tablero, turno_numero)
        turno_numero += 1

        if not ganador:
            turno_actual = "o" if turno_actual == "x" else "x"

        return jsonify(jugada)
    else:
        return jsonify({
            "error": f"Jugada ilegal detectada por el modelo ({turno_actual}). Movimiento: {movimiento}",
            "tablero": tablero
        })

@app.route("/siguiente_partida", methods=["POST"])
def siguiente_partida():
    global tablero, turno_actual, turno_numero, historial, indice_actual

    indice_actual += 1
    tablero = inicializar_tablero()
    turno_actual = "x"
    turno_numero = 1
    historial = []

    return jsonify({"ok": True, "mensaje": "Partida reiniciada y siguiente jugada preparada."})

@app.route("/verificar", methods=["GET"])
def verificar():
    reconstruido = [["b"] * 3 for _ in range(3)]
    for jugada in historial:
        jugador = jugada.get("jugador")
        movimiento = jugada.get("movimiento")
        if not movimiento or len(movimiento) < 3:
            continue
        try:
            fila = int(movimiento[1]) - 1
            col = int(movimiento[2]) - 1
            reconstruido[fila][col] = jugador
        except (IndexError, ValueError):
            continue

    coincide = reconstruido == tablero
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.exists("verificaciones"):
        os.makedirs("verificaciones")

    resultado = {
        "fecha": ahora,
        "tablero_actual": tablero,
        "reconstruido_desde_historial": reconstruido,
        "coincide": coincide
    }

    with open("verificaciones/comparacion_tablero.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)

    return jsonify(resultado)


### FUNCIONES AUXILIARES ###

def guardar_jugada_en_archivo(jugada):
    ruta = "historial_jugadas.txt"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(f"[{now}] Jugador: {jugada['jugador'].upper()}, "
                f"Movimiento: {jugada['movimiento']}, "
                f"Razón: {jugada['razon']}, "
                f"Ganador: {jugada['ganador']}\n")

def guardar_imagen_tablero(tablero, turno):
    if not os.path.exists("tableros"):
        os.makedirs("tableros")

    fig, ax = plt.subplots(figsize=(3, 3))
    ax.set_xticks(np.arange(3))
    ax.set_yticks(np.arange(3))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(True)

    for i in range(3):
        for j in range(3):
            cell = tablero[i][j]
            if cell != "b":
                ax.text(j, 2 - i, cell.upper(), ha="center", va="center", fontsize=28,
                        color="#e74c3c" if cell == "x" else "#2980b9")

    plt.tight_layout()
    nombre = f"tableros/turno_{turno:02d}.png"
    plt.savefig(nombre)
    plt.close()

def evaluar_jugada_rubrica(jugada):
    razon = str(jugada.get("razon", "")).lower()
    return {
        "Comprensión de Reglas": 3 if "legal" in razon or "válido" in razon else 2,
        "Validez y Legalidad": 3 if "válido" in razon else 2,
        "Razonamiento Estratégico": 3 if "bloquear" in razon or "ganar" in razon else 2,
        "Factualidad": 3 if "tablero" in razon or "posición" in razon else 2,
        "Coherencia Explicativa": 3 if "porque" in razon or "ya que" in razon else 2,
        "Claridad Lingüística": 3 if len(razon) > 15 else 2,
        "Adaptabilidad": 3 if "respuesta" in razon or "ajusté" in razon else 2
    }

def cargar_jugadas_desde_archivo():
    if os.path.exists("jugadas.json"):
        with open("jugadas.json", "r") as f:
            return json.load(f)
    return []

def guardar_jugadas_en_archivo(jugadas):
    with open("jugadas.json", "w") as f:
        json.dump(jugadas, f, indent=2)


def cargar_evaluaciones_desde_archivo():
    evaluaciones = []
    try:
        with open("evaluaciones.json", "r", encoding="utf-8") as f:
            for linea in f:
                ev = json.loads(linea)  # <--- esta parte es esencial
                print(type(ev))  # debe mostrar <class 'dict'>
                evaluaciones.append(ev)
    except FileNotFoundError:
        pass
    return evaluaciones

def guardar_evaluacion_en_archivo(evaluacion):
    evaluaciones = cargar_evaluaciones_desde_archivo()
    evaluaciones.append(evaluacion)
    with open("evaluaciones.json", "w", encoding="utf-8") as f:
        json.dump(evaluaciones, f, indent=2, ensure_ascii=False)

def guardar_evaluaciones_completas(match_id, jugadas):
    evaluaciones = [j for j in jugadas if j.get("match_id") == match_id]
    dimensiones = [
        "Comprensión de Reglas", "Validez y Legalidad", "Razonamiento Estratégico",
        "Factualidad", "Coherencia Explicativa", "Claridad Lingüística", "Adaptabilidad"
    ]
    
    for ev in evaluaciones:
        if not ev.get("evaluada", False):
            ev["evaluacion"] = {dim: 0 for dim in dimensiones}
            ev["razon"] = "No evaluada por el usuario"
            ev["evaluada"] = False  # explícito

    with open("evaluaciones.json", "a", encoding="utf-8") as f:
        for ev in evaluaciones:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    
### RUTAS PARA EVALUACIÓN ###

@app.route("/evaluar", methods=["GET", "POST"])
def evaluar():
    jugadas = cargar_jugadas_desde_archivo()

    # Buscar el siguiente match_id con jugadas no evaluadas
    match_ids = sorted(set(j['match_id'] for j in jugadas))
    siguiente_match_id = None
    for mid in match_ids:
        if any(not j.get("evaluada", False) for j in jugadas if j['match_id'] == mid):
            siguiente_match_id = mid
            break

    if siguiente_match_id is None:
        return "No hay jugadas pendientes para evaluar."

    jugadas_del_match = [j for j in jugadas if j['match_id'] == siguiente_match_id]
    jugadas_no_evaluadas = [j for j in jugadas_del_match if not j.get("evaluada", False)]

    if not jugadas_no_evaluadas:
        return redirect(url_for("evaluar"))  # Salto de seguridad

    jugada_actual = jugadas_no_evaluadas[0]

    if request.method == "POST":
        razon = request.form.get('razon', '')
        rubrica = {}
        for key in request.form:
            if key.startswith("rubrica[") and key.endswith("]"):
                dim = key[7:-1]
                rubrica[dim] = int(request.form.get(key))

        # Guardar evaluación en la jugada actual
        for j in jugadas:
            if j['match_id'] == jugada_actual['match_id'] and j['movimiento'] == jugada_actual['movimiento']:
                j['evaluacion'] = rubrica
                j['razon'] = razon
                j['evaluada'] = True
                break

        # Si todas las jugadas del mismo match están evaluadas, guardar en archivo final
        if all(j.get("evaluada", False) for j in jugadas_del_match):
            guardar_evaluaciones_completas(siguiente_match_id, jugadas_del_match)

        guardar_jugadas_en_archivo(jugadas)

        return redirect(url_for("evaluar"))

    return render_template("evaluar.html", jugada=jugada_actual, enumerate=enumerate)



@app.route("/evaluaciones_historial")
def evaluaciones_historial():
    evaluaciones = cargar_evaluaciones_desde_archivo()

    for ev in evaluaciones:
        ev.setdefault("evaluacion", "")
        ev.setdefault("tablero", "")
        ev.setdefault("razon", "")
        ev.setdefault("movimiento", "")
        ev.setdefault("jugador", "")
        ev.setdefault("modelo", "")
        ev.setdefault("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if (isinstance(ev["movimiento"], list) and len(ev["movimiento"]) >= 3
                and ev["movimiento"][0] == "mark"):
            fila = ev["movimiento"][1]
            columna = ev["movimiento"][2]
            ev["movimiento_legible"] = f"Marcar fila {fila}, columna {columna}"
        else:
            ev["movimiento_legible"] = str(ev["movimiento"])

        if isinstance(ev["razon"], list):
            ev["razon_texto"] = "\n".join(ev["razon"])
        elif isinstance(ev["razon"], str):
            ev["razon_texto"] = ev["razon"]
        else:
            ev["razon_texto"] = ""

        if isinstance(ev["tablero"], list):
            ev["tablero"] = ev["tablero"]

    return render_template("evaluaciones_historial.html", evaluaciones=evaluaciones)


@app.route("/rubrica")
def ver_rubrica():
    rubrica = [
        {
            "dimension": "Comprensión de Reglas",
            "nivel1": "Viola reglas básicas: casilla ocupada o fuera del tablero.",
            "nivel2": "Cumple reglas básicas, pero omite situaciones menos evidentes.",
            "nivel3": "Siempre movimientos legales, respeta todas las reglas del turno."
        },
        {
            "dimension": "Validez y Legalidad",
            "nivel1": "Movimiento inválido o ilegal (fuera de límites).",
            "nivel2": "Movimiento válido, sin análisis profundo.",
            "nivel3": "Movimiento válido y elegido tras un análisis completo del tablero."
        },
        {
            "dimension": "Razonamiento Estratégico",
            "nivel1": "Acción sin lógica, aleatoria o contraproducente.",
            "nivel2": "Intención estratégica simple (bloquear/avanzar), sin anticipación.",
            "nivel3": "Justificación clara y anticipada, maximiza chances de ganar."
        },
        {
            "dimension": "Factualidad",
            "nivel1": "Explicación incorrecta o no relacionada con el tablero real.",
            "nivel2": "Justificación generalmente correcta, con imprecisiones menores.",
            "nivel3": "Explicación precisa, basada en hechos concretos del tablero."
        },
        {
            "dimension": "Coherencia Explicativa",
            "nivel1": "Explicación confusa o contradictoria.",
            "nivel2": "Explicación clara pero superficial.",
            "nivel3": "Explicación lógica, completa y alineada con el movimiento."
        },
        {
            "dimension": "Claridad Lingüística",
            "nivel1": "Lenguaje poco claro o con errores graves.",
            "nivel2": "Lenguaje claro con pequeños errores.",
            "nivel3": "Lenguaje preciso, gramaticalmente correcto y fácil de entender."
        },
        {
            "dimension": "Adaptabilidad",
            "nivel1": "Ignora el cambio o jugada previa del oponente.",
            "nivel2": "Se adapta de forma básica o tardía.",
            "nivel3": "Se adapta rápidamente y ajusta su estrategia eficazmente."
        }
    ]
    return render_template("rubrica.html", rubrica=rubrica)

@app.route('/guardar_evaluacion', methods=['POST'])
def guardar_evaluacion():
    jugadas = cargar_jugadas_desde_archivo()

    match_id = int(request.form.get("match_id"))
    razon = request.form.get("razon", "").strip()

    # Capturar valores actualizados desde session
    jugador = session.get("turno_actual", "desconocido")
    modelo = session.get("modelo", "desconocido")
    movimiento = session.get("movimiento", [])
    tablero_actual = session.get("tablero", [["b"]*3 for _ in range(3)])
    ganador = None  # Si tienes un valor de ganador en session, usa session.get("ganador")

    rubrica = {}
    for key in request.form:
        if key.startswith("rubrica[") and key.endswith("]"):
            dim = key[7:-1]
            rubrica[dim] = int(request.form.get(key))

    jugada_actual = None
    for j in jugadas:
        if j['match_id'] == match_id and not j.get("evaluada", False):
            jugada_actual = j
            break

    if jugada_actual:
        # Actualizar todos los campos desde sesión (si quieres que se reescriban con lo último)
        jugada_actual["jugador"] = jugador
        jugada_actual["modelo"] = modelo
        jugada_actual["movimiento"] = movimiento
        jugada_actual["tablero"] = tablero_actual
        jugada_actual["ganador"] = ganador
        jugada_actual["evaluacion"] = rubrica
        jugada_actual["razon"] = razon
        jugada_actual["evaluada"] = True

        jugadas_del_match = [j for j in jugadas if j['match_id'] == match_id]
        if all(j.get("evaluada", False) for j in jugadas_del_match):
            guardar_evaluaciones_completas(match_id, jugadas_del_match)

        # Guardar en evaluaciones.json
        with open("evaluaciones.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(jugada_actual, ensure_ascii=False) + "\n")

        guardar_jugadas_en_archivo(jugadas)

    return redirect(url_for("index"))


@app.route("/siguiente_jugada", methods=["POST"])
def siguiente_jugada():
    # Simplemente redirige a evaluar para mostrar la próxima jugada no evaluada
    return redirect(url_for("evaluar"))


if __name__ == "__main__":
    app.run(debug=True)
