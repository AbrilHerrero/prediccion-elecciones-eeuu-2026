"""Paso 7 — Modelo del Senado.

Usa la misma descomposición que la Cámara:
    cuota D al Senado = cuota D nacional a la Cámara + ventaja del candidato D en ese estado
y modela la ventaja con la inclinación presidencial previa del estado. Solo entran las
elecciones D contra R. Se excluyen las que tuvieron independientes fuertes: aquellas donde los
votos "otros" superaron al candidato D (King en Maine, Osborn en Nebraska, la especial
apartidaria de Mississippi 2018).

Se valida dejando un año afuera, con el clima nacional real del año. Escribe
salidas/validacion_senado.csv: de los residuos sale la incertidumbre por estado que usa
08_prediccion_2026.py.

Uso:  python 07_senado.py
"""

# %% Carga
import pandas as pd

from comun_modelo import (PREDICTORES_SENADO, SALIDAS_MODELO, cargar_tabla_completa,
                          crear_modelo_senado, elecciones_al_senado_d_contra_r,
                          error_medio_en_puntos, estilo, filas_de_entrenamiento,
                          predecir_dejando_un_anio_afuera, titulo)

estilo()
tabla = cargar_tabla_completa()
elecciones_d_contra_r = elecciones_al_senado_d_contra_r(filas_de_entrenamiento(tabla))
print(f"Elecciones al Senado D contra R, 2018–2024: {len(elecciones_d_contra_r)}")
print(elecciones_d_contra_r.groupby("year").size().to_string())

# %% 1. Validación dejando un año afuera
titulo("1. VALIDACIÓN (dejando un año afuera)")
ventaja_prevista = predecir_dejando_un_anio_afuera(crear_modelo_senado(), elecciones_d_contra_r,
                                                   PREDICTORES_SENADO,
                                                   "ventaja_candidato_d_senado")
cuota_prevista = elecciones_d_contra_r["nat_house_dem_share_2p"] + ventaja_prevista
cuota_real = elecciones_d_contra_r["senate_dem_share_2p"]
ganador_acertado = (cuota_prevista > 0.5) == (cuota_real > 0.5)
residuo = cuota_real - cuota_prevista

resumen_por_anio = pd.DataFrame({
    "elecciones": ganador_acertado.groupby(elecciones_d_contra_r["year"]).size(),
    "ganador_acertado": ganador_acertado.groupby(elecciones_d_contra_r["year"]).sum(),
    "error_medio_pp": (residuo.abs() * 100).groupby(elecciones_d_contra_r["year"]).mean(),
})
print(resumen_por_anio.round(2).to_string())
desvio_del_residuo = residuo.std()
print(f"\nError absoluto medio: {error_medio_en_puntos(cuota_prevista, cuota_real):.2f} pp")
print(f"Ganador acertado: {ganador_acertado.sum()} de {len(ganador_acertado)} "
      f"({ganador_acertado.mean():.0%})")
print(f"Desvío del residuo: {desvio_del_residuo * 100:.2f} pp  -> incertidumbre por estado en 08")

print("\nElecciones donde el modelo erró el ganador:")
erradas = elecciones_d_contra_r.assign(prevista=cuota_prevista)[~ganador_acertado]
print(erradas[["year", "state", "senate_dem_share_2p", "prevista"]].round(3)
      .to_string(index=False))
print("Son, casi todas, elecciones cerradas o con candidatos que se apartan de su partido")
print("(efecto candidato), que un modelo de fundamentos no puede ver.")

validacion = elecciones_d_contra_r[["year", "state", "senate_dem_share_2p"]].assign(
    cuota_prevista=cuota_prevista, residuo=residuo)
validacion.round(4).to_csv(SALIDAS_MODELO / "validacion_senado.csv", index=False)

# %% 2. Modelo final
titulo("2. MODELO FINAL (entrenado con 2018–2024)")
modelo_senado = crear_modelo_senado().fit(elecciones_d_contra_r[PREDICTORES_SENADO],
                                          elecciones_d_contra_r["ventaja_candidato_d_senado"])
print(f"  inclinación presidencial previa   {modelo_senado.coef_[0]:+.3f}")
print(f"  constante                         {modelo_senado.intercept_:+.4f}")
print("Un coeficiente menor que 1 indica que los candidatos al Senado se apartan un poco menos")
print("que el voto presidencial de la inclinación de su estado.")
