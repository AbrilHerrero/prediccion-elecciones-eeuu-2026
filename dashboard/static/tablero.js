// Tablero de la predicción 2026: pide los datos a la API y dibuja controles, indicadores,
// gráficos, mapa y tablas. Sin librerías externas.

const formatoPorcentaje = new Intl.NumberFormat("es-AR", { style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1 });
const formatoPorcentajeEntero = new Intl.NumberFormat("es-AR", { style: "percent", maximumFractionDigits: 0 });
const formatoUnDecimal = new Intl.NumberFormat("es-AR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const formatoEntero = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 });

// Posición (fila, columna) de cada estado en el mapa de mosaicos.
const POSICION_EN_EL_MAPA = {
  AK: [0, 0], ME: [0, 10],
  WI: [1, 5], VT: [1, 9], NH: [1, 10],
  WA: [2, 0], ID: [2, 1], MT: [2, 2], ND: [2, 3], MN: [2, 4], IL: [2, 5], MI: [2, 6], NY: [2, 8], MA: [2, 9],
  OR: [3, 0], NV: [3, 1], WY: [3, 2], SD: [3, 3], IA: [3, 4], IN: [3, 5], OH: [3, 6], PA: [3, 7], NJ: [3, 8], CT: [3, 9], RI: [3, 10],
  CA: [4, 0], UT: [4, 1], CO: [4, 2], NE: [4, 3], MO: [4, 4], KY: [4, 5], WV: [4, 6], VA: [4, 7], MD: [4, 8], DE: [4, 9],
  AZ: [5, 1], NM: [5, 2], KS: [5, 3], AR: [5, 4], TN: [5, 5], NC: [5, 6], SC: [5, 7],
  OK: [6, 3], LA: [6, 4], MS: [6, 5], AL: [6, 6], GA: [6, 7],
  HI: [7, 0], TX: [7, 3], FL: [7, 8],
};

const estado = {
  contexto: null,
  barrido: [],
  prediccionActual: null,
  vistaDelMapa: "camara",
  columnaDeOrden: "camara_cuota_d_prevista",
  ordenDescendente: true,
  gananciaInicialPp: 0,
};

const elemento = (id) => document.getElementById(id);
const tooltip = elemento("tooltip");

// ---------------------------------------------------------------------------- utilidades

async function pedirJson(ruta) {
  const respuesta = await fetch(ruta);
  if (!respuesta.ok) throw new Error(`${ruta}: ${respuesta.status}`);
  return respuesta.json();
}

function colorDeLaPaleta(nombreDeVariable) {
  return getComputedStyle(document.documentElement).getPropertyValue(nombreDeVariable).trim();
}

function hexARgb(hex) {
  const valor = parseInt(hex.replace("#", ""), 16);
  return [(valor >> 16) & 255, (valor >> 8) & 255, valor & 255];
}

function mezclarColores(colorA, colorB, proporcion) {
  const [a, b] = [hexARgb(colorA), hexARgb(colorB)];
  const canal = (i) => Math.round(a[i] + (b[i] - a[i]) * proporcion);
  return `rgb(${canal(0)}, ${canal(1)}, ${canal(2)})`;
}

// Escala divergente: 0 = rojo, 0,5 = gris neutro, 1 = azul.
function colorDivergente(valorEntreCeroYUno) {
  const acotado = Math.min(1, Math.max(0, valorEntreCeroYUno));
  const neutro = colorDeLaPaleta("--neutro-medio");
  if (acotado < 0.5) return mezclarColores(colorDeLaPaleta("--republicano"), neutro, acotado / 0.5);
  return mezclarColores(neutro, colorDeLaPaleta("--democrata"), (acotado - 0.5) / 0.5);
}

function textoDeGanancia(ganancia) {
  const signo = ganancia > 0 ? "+" : ganancia < 0 ? "−" : "±";
  return `${signo}${formatoUnDecimal.format(Math.abs(ganancia))} pp`;
}

function mostrarTooltip(evento, html) {
  tooltip.innerHTML = html;
  tooltip.hidden = false;
  const margen = 14;
  const ancho = tooltip.offsetWidth;
  const izquierda = evento.clientX + margen + ancho > window.innerWidth
    ? evento.clientX - margen - ancho : evento.clientX + margen;
  tooltip.style.left = `${izquierda}px`;
  tooltip.style.top = `${evento.clientY + margen}px`;
}

function ocultarTooltip() { tooltip.hidden = true; }

function crearElementoSvg(etiqueta, atributos = {}) {
  const nodo = document.createElementNS("http://www.w3.org/2000/svg", etiqueta);
  for (const [nombre, valor] of Object.entries(atributos)) nodo.setAttribute(nombre, valor);
  return nodo;
}

// ---------------------------------------------------------------------------- controles

function prepararControles() {
  const { contexto } = estado;
  const deslizador = elemento("deslizador-clima");
  deslizador.min = contexto.ganancia_minima_pp;
  deslizador.max = contexto.ganancia_maxima_pp;
  const escenarioCentral = contexto.escenarios.find((e) => e.nombre === contexto.escenario_central);
  deslizador.value = Math.round(escenarioCentral.ganancia_democrata_pp * 2) / 2;
  estado.gananciaInicialPp = escenarioCentral.ganancia_democrata_pp;

  const contenedorBotones = elemento("botones-escenario");
  for (const escenario of contexto.escenarios) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "chip";
    boton.textContent = `${escenario.nombre} (${textoDeGanancia(escenario.ganancia_democrata_pp)})`;
    boton.dataset.ganancia = escenario.ganancia_democrata_pp;
    boton.addEventListener("click", () => {
      deslizador.value = Math.round(escenario.ganancia_democrata_pp * 2) / 2;
      actualizarPrediccion(escenario.ganancia_democrata_pp);
    });
    contenedorBotones.appendChild(boton);
  }

  let temporizador = null;
  deslizador.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => actualizarPrediccion(Number(deslizador.value)), 120);
  });

  const perdidas = Object.entries(contexto.perdidas_del_presidente_en_medio_termino)
    .map(([anio, perdida]) => `${anio}: ${textoDeGanancia(perdida * 100)}`).join(" · ");
  elemento("antecedentes").textContent =
    `Cambio del partido del presidente en los medio término del panel: ${perdidas}. ` +
    `Cuota D nacional 2024: ${formatoPorcentaje.format(contexto.cuota_nacional_2024)}.`;

  for (const boton of document.querySelectorAll("[data-vista-mapa]")) {
    boton.addEventListener("click", () => {
      estado.vistaDelMapa = boton.dataset.vistaMapa;
      for (const otro of document.querySelectorAll("[data-vista-mapa]")) {
        otro.classList.toggle("activo", otro === boton);
      }
      dibujarMapa();
    });
  }

  for (const encabezado of document.querySelectorAll("#tabla-estados th")) {
    encabezado.addEventListener("click", () => {
      const columna = encabezado.dataset.columna;
      estado.ordenDescendente = estado.columnaDeOrden === columna ? !estado.ordenDescendente : true;
      estado.columnaDeOrden = columna;
      dibujarTablaDeEstados();
    });
  }

  elemento("boton-tema").addEventListener("click", () => {
    const raiz = document.documentElement;
    const oscuroAhora = raiz.dataset.theme
      ? raiz.dataset.theme === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    raiz.dataset.theme = oscuroAhora ? "light" : "dark";
    dibujarTodo();
  });
}

async function actualizarPrediccion(gananciaPp) {
  estado.prediccionActual = await pedirJson(`/api/prediccion?ganancia_democrata_pp=${gananciaPp}`);
  dibujarTodo();
}

// ---------------------------------------------------------------------------- dibujo

function dibujarTodo() {
  if (!estado.prediccionActual) return;
  dibujarIndicadores();
  dibujarBarrido("grafico-barrido-camara", "camara_bancas_d_esperadas", estado.contexto.bancas_para_mayoria_camara, true);
  dibujarBarrido("grafico-barrido-senado", "senado_bancas_d_esperadas", estado.contexto.bancas_para_mayoria_senado, false);
  dibujarMapa();
  dibujarListaDelSenado();
  dibujarTablaDeEstados();
}

function dibujarBarraDeBancas(idContenedor, bancasD, totalDeBancas, mayoria) {
  const contenedor = elemento(idContenedor);
  const proporcionD = Math.min(1, Math.max(0, bancasD / totalDeBancas));
  contenedor.innerHTML =
    `<div class="tramo-d" style="width:${proporcionD * 100}%"></div><div class="tramo-r"></div>` +
    `<div class="marca-mayoria" style="left:${(mayoria / totalDeBancas) * 100}%"></div>`;
  contenedor.setAttribute("aria-label",
    `${formatoEntero.format(bancasD)} bancas D y ${formatoEntero.format(totalDeBancas - bancasD)} R; mayoría ${mayoria}`);
}

function dibujarIndicadores() {
  const { resumen } = estado.prediccionActual;
  const { contexto } = estado;
  const ganancia = resumen.ganancia_democrata * 100;
  elemento("valor-ganancia").textContent = textoDeGanancia(ganancia);
  elemento("valor-cuota-nacional").textContent = `cuota D nacional ${formatoPorcentaje.format(resumen.cuota_d_nacional)}`;

  for (const boton of document.querySelectorAll("#botones-escenario .chip")) {
    boton.classList.toggle("activo", Math.abs(Number(boton.dataset.ganancia) - ganancia) < 0.26);
  }

  const bancasCamara = resumen.camara_bancas_d_esperadas;
  const mayoriaCamara = contexto.bancas_para_mayoria_camara;
  elemento("indicador-camara").textContent = formatoEntero.format(bancasCamara);
  elemento("indicador-camara-rango").textContent =
    `Rango histórico ${formatoEntero.format(resumen.camara_rango_inferior)}–${formatoEntero.format(resumen.camara_rango_superior)} · ` +
    (bancasCamara >= mayoriaCamara ? `mayoría D (${mayoriaCamara})` : `${formatoEntero.format(mayoriaCamara - bancasCamara)} por debajo de la mayoría`);
  dibujarBarraDeBancas("barra-camara", bancasCamara, 435, mayoriaCamara);

  const bancasSenado = resumen.senado_bancas_d_esperadas;
  elemento("indicador-senado").textContent = formatoUnDecimal.format(bancasSenado);
  elemento("indicador-senado-detalle").textContent =
    `${contexto.senadores_que_no_renuevan.D} D no renuevan · mayoría D: ${contexto.bancas_para_mayoria_senado}`;
  dibujarBarraDeBancas("barra-senado", bancasSenado, 100, contexto.bancas_para_mayoria_senado);

  elemento("indicador-control-senado").textContent = formatoPorcentajeEntero.format(resumen.senado_probabilidad_control_d);
}

function dibujarBarrido(idContenedor, columna, mayoria, conFranja) {
  const contenedor = elemento(idContenedor);
  const ancho = 460, alto = 250;
  const margen = { arriba: 12, derecha: 16, abajo: 34, izquierda: 44 };
  const puntos = estado.barrido;
  const valores = puntos.map((p) => p[columna]);
  const minimos = conFranja ? puntos.map((p) => p.camara_rango_inferior) : valores;
  const maximos = conFranja ? puntos.map((p) => p.camara_rango_superior) : valores;
  const valorMinimo = Math.min(...minimos, mayoria) - 2;
  const valorMaximo = Math.max(...maximos, mayoria) + 2;
  const gananciaMinima = puntos[0].ganancia_democrata_pp;
  const gananciaMaxima = puntos[puntos.length - 1].ganancia_democrata_pp;

  const x = (ganancia) => margen.izquierda + ((ganancia - gananciaMinima) / (gananciaMaxima - gananciaMinima)) * (ancho - margen.izquierda - margen.derecha);
  const y = (valor) => alto - margen.abajo - ((valor - valorMinimo) / (valorMaximo - valorMinimo)) * (alto - margen.arriba - margen.abajo);

  const svg = crearElementoSvg("svg", { viewBox: `0 0 ${ancho} ${alto}`, role: "img",
    "aria-label": `Bancas D esperadas según el clima nacional, de ${textoDeGanancia(gananciaMinima)} a ${textoDeGanancia(gananciaMaxima)}` });

  const pasoEje = (valorMaximo - valorMinimo) > 40 ? 20 : 2;
  for (let valor = Math.ceil(valorMinimo / pasoEje) * pasoEje; valor <= valorMaximo; valor += pasoEje) {
    svg.appendChild(crearElementoSvg("line", { x1: margen.izquierda, x2: ancho - margen.derecha, y1: y(valor), y2: y(valor), class: "linea-grilla" }));
    const etiqueta = crearElementoSvg("text", { x: margen.izquierda - 6, y: y(valor) + 4, "text-anchor": "end" });
    etiqueta.textContent = valor;
    svg.appendChild(etiqueta);
  }
  for (let ganancia = Math.ceil(gananciaMinima / 2) * 2; ganancia <= gananciaMaxima; ganancia += 2) {
    const etiqueta = crearElementoSvg("text", { x: x(ganancia), y: alto - margen.abajo + 16, "text-anchor": "middle" });
    etiqueta.textContent = textoDeGanancia(ganancia).replace(" pp", "");
    svg.appendChild(etiqueta);
  }
  const tituloEjeX = crearElementoSvg("text", { x: (margen.izquierda + ancho - margen.derecha) / 2, y: alto - 4, "text-anchor": "middle" });
  tituloEjeX.textContent = "corrimiento nacional hacia los D (pp)";
  svg.appendChild(tituloEjeX);

  if (conFranja) {
    const borde = puntos.map((p) => `${x(p.ganancia_democrata_pp)},${y(p.camara_rango_superior)}`)
      .concat([...puntos].reverse().map((p) => `${x(p.ganancia_democrata_pp)},${y(p.camara_rango_inferior)}`));
    svg.appendChild(crearElementoSvg("polygon", { points: borde.join(" "), class: "franja" }));
  }
  svg.appendChild(crearElementoSvg("line", { x1: margen.izquierda, x2: ancho - margen.derecha, y1: y(mayoria), y2: y(mayoria), class: "linea-mayoria" }));
  svg.appendChild(crearElementoSvg("polyline", {
    points: puntos.map((p) => `${x(p.ganancia_democrata_pp)},${y(p[columna])}`).join(" "), class: "linea-serie" }));

  const gananciaActual = estado.prediccionActual.resumen.ganancia_democrata * 100;
  const valorActual = estado.prediccionActual.resumen[columna];
  svg.appendChild(crearElementoSvg("line", { x1: x(gananciaActual), x2: x(gananciaActual), y1: margen.arriba, y2: alto - margen.abajo, class: "marca-actual" }));
  svg.appendChild(crearElementoSvg("circle", { cx: x(gananciaActual), cy: y(valorActual), r: 5, class: "punto-actual" }));

  // Capa de interacción: cruz vertical + tooltip con el punto más cercano.
  const cruz = crearElementoSvg("line", { y1: margen.arriba, y2: alto - margen.abajo, class: "cruz", visibility: "hidden" });
  svg.appendChild(cruz);
  const capa = crearElementoSvg("rect", { x: margen.izquierda, y: margen.arriba, width: ancho - margen.izquierda - margen.derecha,
    height: alto - margen.arriba - margen.abajo, fill: "transparent" });
  capa.addEventListener("mousemove", (evento) => {
    const caja = svg.getBoundingClientRect();
    const xEnSvg = ((evento.clientX - caja.left) / caja.width) * ancho;
    const masCercano = puntos.reduce((mejor, p) => Math.abs(x(p.ganancia_democrata_pp) - xEnSvg) < Math.abs(x(mejor.ganancia_democrata_pp) - xEnSvg) ? p : mejor);
    cruz.setAttribute("x1", x(masCercano.ganancia_democrata_pp));
    cruz.setAttribute("x2", x(masCercano.ganancia_democrata_pp));
    cruz.setAttribute("visibility", "visible");
    const detalle = conFranja
      ? `${formatoEntero.format(masCercano[columna])} bancas D (rango ${formatoEntero.format(masCercano.camara_rango_inferior)}–${formatoEntero.format(masCercano.camara_rango_superior)})`
      : `${formatoUnDecimal.format(masCercano[columna])} bancas D · control D ${formatoPorcentajeEntero.format(masCercano.senado_probabilidad_control_d)}`;
    mostrarTooltip(evento, `<strong>${textoDeGanancia(masCercano.ganancia_democrata_pp)}</strong> · cuota D nacional ${formatoPorcentaje.format(masCercano.cuota_d_nacional)}<br>${detalle}`);
  });
  capa.addEventListener("mouseleave", () => { cruz.setAttribute("visibility", "hidden"); ocultarTooltip(); });
  capa.addEventListener("click", (evento) => {
    const caja = svg.getBoundingClientRect();
    const xEnSvg = ((evento.clientX - caja.left) / caja.width) * ancho;
    const masCercano = puntos.reduce((mejor, p) => Math.abs(x(p.ganancia_democrata_pp) - xEnSvg) < Math.abs(x(mejor.ganancia_democrata_pp) - xEnSvg) ? p : mejor);
    elemento("deslizador-clima").value = masCercano.ganancia_democrata_pp;
    actualizarPrediccion(masCercano.ganancia_democrata_pp);
  });
  svg.appendChild(capa);

  contenedor.replaceChildren(svg);
}

function detalleDeEstadoEnHtml(fila) {
  let html = `<strong>${fila.state_name}</strong><br>Cámara: cuota D ${formatoPorcentaje.format(fila.camara_cuota_d_prevista)} · ` +
    `${formatoUnDecimal.format(fila.camara_bancas_d_esperadas)} de ${fila.house_seats} bancas D`;
  if (fila.senado_probabilidad_victoria_d !== null) {
    html += `<br>Senado: cuota D ${formatoPorcentaje.format(fila.senado_cuota_d_prevista)} · ` +
      `prob. victoria D ${formatoPorcentajeEntero.format(fila.senado_probabilidad_victoria_d)}`;
  }
  if (fila.mapa_nuevo_2026) html += "<br><em>Mapa de distritos nuevo en 2026</em>";
  return html;
}

function dibujarMapa() {
  const contenedor = elemento("mapa-de-estados");
  const vistaCamara = estado.vistaDelMapa === "camara";
  const mosaicos = estado.prediccionActual.estados.map((fila) => {
    const [filaEnMapa, columnaEnMapa] = POSICION_EN_EL_MAPA[fila.state];
    const mosaico = document.createElement("div");
    mosaico.className = "mosaico" + (fila.mapa_nuevo_2026 && vistaCamara ? " mapa-nuevo" : "");
    mosaico.style.gridRow = filaEnMapa + 1;
    mosaico.style.gridColumn = columnaEnMapa + 1;

    const valor = vistaCamara ? fila.camara_cuota_d_prevista : fila.senado_probabilidad_victoria_d;
    if (valor === null) {
      mosaico.classList.add("sin-eleccion");
      mosaico.innerHTML = `${fila.state}`;
    } else {
      // Cámara: 35 %–65 % ocupa toda la escala; Senado: la probabilidad va de 0 a 1.
      const posicionEnEscala = vistaCamara ? (valor - 0.35) / 0.3 : valor;
      mosaico.style.background = colorDivergente(posicionEnEscala);
      mosaico.style.color = Math.abs(posicionEnEscala - 0.5) > 0.3 ? "#ffffff" : colorDeLaPaleta("--texto-principal");
      mosaico.innerHTML = `${fila.state}<span>${formatoPorcentajeEntero.format(valor)}</span>`;
    }
    mosaico.addEventListener("mousemove", (evento) => mostrarTooltip(evento, detalleDeEstadoEnHtml(fila)));
    mosaico.addEventListener("mouseleave", ocultarTooltip);
    return mosaico;
  });
  contenedor.replaceChildren(...mosaicos);
  elemento("titulo-mapa").textContent = vistaCamara ? "Cuota D prevista a la Cámara" : "Probabilidad de victoria D en el Senado";
  elemento("leyenda-mapa").innerHTML = vistaCamara
    ? `<span>≤35 % D</span><div class="degrade"></div><span>≥65 % D</span>`
    : `<span>gana R</span><div class="degrade"></div><span>gana D</span>`;
}

function dibujarListaDelSenado() {
  const elecciones = estado.prediccionActual.estados
    .filter((fila) => fila.senado_probabilidad_victoria_d !== null)
    .sort((a, b) => b.senado_probabilidad_victoria_d - a.senado_probabilidad_victoria_d);
  const filas = elecciones.map((fila) => {
    const probabilidad = fila.senado_probabilidad_victoria_d;
    // Color del partido favorito; cuanto más pareja la elección, más tenue (nunca invisible).
    const colorDelFavorito = colorDeLaPaleta(probabilidad >= 0.5 ? "--democrata" : "--republicano");
    const opacidad = 0.35 + 0.65 * Math.abs(probabilidad - 0.5) * 2;
    const contenedorFila = document.createElement("div");
    contenedorFila.className = "fila-senado";
    contenedorFila.innerHTML =
      `<span>${fila.state_name}${fila.state === "NE" ? " *" : ""}</span>` +
      `<div class="pista"><div class="relleno" style="width:${probabilidad * 100}%;background:${colorDelFavorito};opacity:${opacidad}"></div><div class="mitad"></div></div>` +
      `<span class="numero">${formatoPorcentajeEntero.format(probabilidad)}</span>`;
    contenedorFila.addEventListener("mousemove", (evento) => mostrarTooltip(evento, detalleDeEstadoEnHtml(fila)));
    contenedorFila.addEventListener("mouseleave", ocultarTooltip);
    return contenedorFila;
  });
  elemento("lista-senado").replaceChildren(...filas);
}

function celdaNumerica(valor, formato) {
  return `<td class="numero">${valor === null ? "—" : formato.format(valor)}</td>`;
}

function dibujarTablaDeEstados() {
  const { columnaDeOrden, ordenDescendente } = estado;
  const filas = [...estado.prediccionActual.estados].sort((a, b) => {
    const [valorA, valorB] = [a[columnaDeOrden], b[columnaDeOrden]];
    if (valorA === null) return 1;
    if (valorB === null) return -1;
    const comparacion = typeof valorA === "string" ? valorA.localeCompare(valorB, "es") : valorA - valorB;
    return ordenDescendente ? -comparacion : comparacion;
  });
  document.querySelector("#tabla-estados tbody").innerHTML = filas.map((fila) =>
    `<tr><td>${fila.state_name}</td>` +
    celdaNumerica(fila.house_seats, formatoEntero) +
    celdaNumerica(fila.camara_cuota_d_prevista, formatoPorcentaje) +
    celdaNumerica(fila.camara_bancas_d_esperadas, formatoUnDecimal) +
    celdaNumerica(fila.senado_cuota_d_prevista, formatoPorcentaje) +
    celdaNumerica(fila.senado_probabilidad_victoria_d, formatoPorcentajeEntero) +
    `<td>${fila.mapa_nuevo_2026 ? "sí" : ""}</td></tr>`).join("");
  for (const encabezado of document.querySelectorAll("#tabla-estados th")) {
    const flecha = encabezado.dataset.columna === columnaDeOrden ? (ordenDescendente ? " ↓" : " ↑") : "";
    encabezado.textContent = encabezado.textContent.replace(/ [↓↑]$/, "") + flecha;
  }
}

function dibujarTablasDeValidacion() {
  const { contexto } = estado;
  document.querySelector("#tabla-modelos tbody").innerHTML = contexto.comparacion_de_modelos.map((fila) =>
    `<tr><td>${fila.metodo}${fila.tipo === "línea base" ? " <em>(línea base)</em>" : ""}</td>` +
    `<td class="numero">${formatoUnDecimal.format(fila.error_todos_pp)} pp</td>` +
    `<td class="numero">${formatoUnDecimal.format(fila.error_solo_disputados_pp)} pp</td></tr>`).join("");
  document.querySelector("#tabla-bancas tbody").innerHTML = contexto.validacion_bancas.map((fila) => {
    const diferencia = fila.B_cadena_completa - fila.bancas_d_reales;
    return `<tr><td>${fila.year}</td><td class="numero">${fila.bancas_d_reales}</td>` +
      `<td class="numero">${formatoEntero.format(fila.B_cadena_completa)}</td>` +
      `<td class="numero">${diferencia > 0 ? "+" : "−"}${formatoEntero.format(Math.abs(diferencia))}</td></tr>`;
  }).join("");
}

// ---------------------------------------------------------------------------- inicio

async function iniciar() {
  [estado.contexto, estado.barrido] = await Promise.all([pedirJson("/api/contexto"), pedirJson("/api/barrido")]);
  prepararControles();
  dibujarTablasDeValidacion();
  await actualizarPrediccion(estado.gananciaInicialPp);
}

iniciar().catch((error) => {
  document.querySelector("main").insertAdjacentHTML("afterbegin",
    `<section class="tarjeta"><strong>No se pudieron cargar los datos.</strong> ${error.message}</section>`);
});
