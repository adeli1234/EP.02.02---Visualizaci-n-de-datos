# Práctica 8B: más variables de la API y más gráficas
# Herramientas de Visualización · IDIA224 · Unidad II
#
#     pip install requests pandas matplotlib seaborn
#     python practica8b_mas_variables.py
#
# Mismo endpoint de la práctica anterior, pero ahora pedimos ocho variables
# en lugar de tres, y cada gráfica responde una pregunta distinta.
 
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
 
# ─── Paleta del curso ──────────────────────────────────────────────────
GRIS = "#B9C3D1"
AZUL = "#1C4C9A"
ROJO = "#B2182B"
NARANJA = "#E69F00"
sns.set_theme(style="whitegrid")
 
# ─── Qué le pedimos a la API ───────────────────────────────────────────
CIUDADES = {
    "Morelia":   (19.7008, -101.1844),
    "Querétaro": (20.5888, -100.3899),
}
CIUDAD = "Morelia"
 
# Las variables van en una sola cadena, separadas por comas y sin espacios.
VARIABLES = [
    "temperature_2m_max",            # máxima del día
    "temperature_2m_min",            # mínima del día
    "temperature_2m_mean",           # promedio del día
    "apparent_temperature_max",      # sensación térmica máxima
    "precipitation_sum",             # lluvia acumulada, en mm
    "precipitation_hours",           # cuántas horas llovió
    "windspeed_10m_max",             # viento máximo a 10 m de altura
    "shortwave_radiation_sum",       # radiación solar recibida
]

latitud, longitud = CIUDADES[CIUDAD]
 
respuesta = requests.get(
    "https://archive-api.open-meteo.com/v1/archive",
    params={
        "latitude": latitud,
        "longitude": longitud,
        "start_date": "2021-01-01",
        "end_date": "2025-12-31",
        "daily": ",".join(VARIABLES),
        "timezone": "America/Mexico_City",
    },
    timeout=60,
)
 
print("Código de estado:", respuesta.status_code)
respuesta.raise_for_status()
datos = respuesta.json()
 
# Las unidades SIEMPRE se leen de la respuesta, nunca se escriben a mano.
unidades = datos["daily_units"]
print("Unidades que devolvió la API:")
for variable, unidad in unidades.items():
    print("   ", variable, "->", unidad)
 
 
# ─── De JSON a tabla ───────────────────────────────────────────────────
df = pd.DataFrame(datos["daily"])
df["time"] = pd.to_datetime(df["time"])
 
df = df.rename(columns={
    "time": "Fecha",
    "temperature_2m_max": "TempMax",
    "temperature_2m_min": "TempMin",
    "temperature_2m_mean": "TempMedia",
    "apparent_temperature_max": "Sensacion",
    "precipitation_sum": "Lluvia",
    "precipitation_hours": "HorasLluvia",
    "windspeed_10m_max": "Viento",
    "shortwave_radiation_sum": "Radiacion",
})
 
df["Anio"] = df["Fecha"].dt.year
df["Mes"] = df["Fecha"].dt.month
 
# Información derivada: lo que la API no trae pero se calcula
df["Amplitud"] = df["TempMax"] - df["TempMin"]          # cuánto varía el día
df["Temporada"] = df["Mes"].apply(
    lambda m: "Lluvias" if 6 <= m <= 10 else "Secas")
 
print("\nFilas y columnas:", df.shape)
print("Periodo:", df["Fecha"].min().date(), "a", df["Fecha"].max().date())
print("\nFaltantes por columna:")
print(df.isna().sum())
 
print("\nResumen por temporada:")
print(df.groupby("Temporada")[["TempMax", "Amplitud", "Lluvia", "Radiacion"]]
        .mean().round(2).to_string())
 
 
# ─── Gráfica 1 · La banda de temperatura del año ───────────────────────
# Pregunta: ¿entre qué valores se mueve el día?
ultimo = df[df["Anio"] == df["Anio"].max()]
 
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.fill_between(ultimo["Fecha"], ultimo["TempMin"], ultimo["TempMax"],
                color=GRIS, label="Entre la mínima y la máxima")
ax.plot(ultimo["Fecha"], ultimo["TempMedia"], color=AZUL, linewidth=1.5,
        label="Temperatura media")
ax.set_title(f"El día más frío y el más caluroso de cada fecha en {CIUDAD}")
ax.set_xlabel("Fecha")
ax.set_ylabel(f"Temperatura ({unidades['temperature_2m_max']})")
ax.legend(frameon=False)
fig.savefig("output/g1_banda_termica.png", dpi=150, bbox_inches="tight")
 
 
# ─── Gráfica 2 · Cuánto llueve y cuántas horas ─────────────────────────
# Pregunta: ¿llueve mucho de golpe o poquito muchas veces?
mensual = df.groupby("Mes").agg(
    Lluvia=("Lluvia", "sum"),
    Horas=("HorasLluvia", "sum"),
)
anios = df["Anio"].nunique()
mensual = mensual / anios        # promedio por año
 
fig, ax = plt.subplots(figsize=(10, 4.5))
colores = [AZUL if v == mensual["Lluvia"].max() else GRIS
           for v in mensual["Lluvia"]]
ax.bar(mensual.index, mensual["Lluvia"], color=colores)
ax.set_title("La lluvia del año se concentra en unos pocos meses")
ax.set_xlabel("Mes")
ax.set_ylabel(f"Lluvia acumulada ({unidades['precipitation_sum']})")
ax.set_xticks(range(1, 13))
 
# Segundo eje: las horas de lluvia, que es otra unidad
eje2 = ax.twinx()
eje2.plot(mensual.index, mensual["Horas"], color=ROJO, linewidth=2,
          marker="o", markersize=4)
eje2.set_ylabel("Horas con lluvia", color=ROJO)
eje2.grid(False)
fig.savefig("output/g2_lluvia_y_horas.png", dpi=150, bbox_inches="tight")
 
 
# ─── Gráfica 3 · Qué tanto cambia la temperatura dentro del día ────────
# Pregunta: ¿en qué meses hay más diferencia entre el día y la noche?
fig, ax = plt.subplots(figsize=(10, 4.5))
sns.boxplot(data=df, x="Mes", y="Amplitud", color=GRIS, ax=ax)
ax.set_title("En la temporada de secas el día y la noche se parecen menos")
ax.set_xlabel("Mes")
ax.set_ylabel(f"Diferencia entre máxima y mínima ({unidades['temperature_2m_max']})")
fig.savefig("output/g3_amplitud.png", dpi=150, bbox_inches="tight")

# ─── Gráfica 4 - Radiación y temperatura ───────────────────────────────
# Pregunta: ¿qué relación hay entre la radiación solar y la temperatura?

fig, ax = plt.subplots(figsize=(10, 4.5))
sns.scatterplot(data=df, x="Radiacion", y="TempMax", color=AZUL, alpha=0.5, ax=ax)
ax.set_title("La radiación solar y la temperatura máxima del día")
ax.set_xlabel(f"Radiación solar ({unidades['shortwave_radiation_sum']})")
ax.set_ylabel(f"Temperatura máxima ({unidades['temperature_2m_max']})")
fig.savefig("output/g4_radiacion_temp.png", dpi=150, bbox_inches="tight")

# ─── Gráfica 5 - Mapa de calor mes por año ──────────────────────────────
# Pregunta: ¿qué meses son más calurosos y cuáles más fríos?
pivot = df.pivot_table(index="Anio", columns="Mes", values="TempMedia")
fig, ax = plt.subplots(figsize=(10, 4.5))
sns.heatmap(pivot, cmap="YlOrRd", annot=True, fmt=".1f", linewidths=0.5, ax=ax)
ax.set_title("Temperatura media por mes y año")
ax.set_xlabel("Mes")
ax.set_ylabel("Año")
fig.savefig("output/g5_mapa_calor.png", dpi=150, bbox_inches="tight")

# streamlit sirve para crear aplicaciones web interactivas de manera sencilla,
# especialmente para la visualización de datos. Permite a los usuarios
# interactuar con gráficos, tablas y otros elementos visuales sin necesidad de
# conocimientos avanzados en desarrollo web.

# Aporta interactividad a las gráficas, permitiendo a los usuarios filtrar datos,