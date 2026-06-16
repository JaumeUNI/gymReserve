/* GymReserve — lógica del frontend
 *
 * Una sola página con varias "vistas" (divs) que se muestran/ocultan.
 * L'autenticació funciona amb una COOKIE: quan fas login, el servidor desa el
 * token JWT en una cookie i el navegador la torna a enviar sola en cada petició.
 * Per això aquí no guardem cap token; només guardem qui és l'usuari per pintar el menú.
 */

const API = "/api/v1";

// Només guardem les dades de l'usuari (nom, rol) per saber què mostrar al menú.
// El token NO el guardem: viatja sol dins la cookie.
let sessio = { usuari: null };


// ---------- Llamada genérica a la API ----------
async function api(ruta, metode = "GET", cos = null) {
  const opcions = {
    method: metode,
    headers: {},
    credentials: "same-origin",   // important: fa que el navegador enviï la cookie
  };
  if (cos) {
    opcions.headers["Content-Type"] = "application/json";
    opcions.body = JSON.stringify(cos);
  }
  const resp = await fetch(API + ruta, opcions);
  if (resp.status === 204) return null;            // sin contenido (DELETE/logout)
  const dades = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dades.detail || "Hi ha hagut un error");
  return dades;
}


// ---------- Navegación entre vistas ----------
function mostrarVista(id) {
  document.querySelectorAll(".vista").forEach(v => v.classList.remove("activa"));
  document.getElementById(id).classList.add("activa");
  window.scrollTo(0, 0);
}

function avis(text, tipus = "ok") {
  const el = document.getElementById("avis");
  el.textContent = text;
  el.className = "avis " + tipus;
  setTimeout(() => { el.className = "avis"; }, 3500);
}


// ---------- Sesión: actualizar la barra de navegación ----------
function refrescarNav() {
  const nav = document.getElementById("nav");
  if (sessio.usuari) {
    const admin = sessio.usuari.rol === "admin";
    nav.innerHTML = `
      ${admin ? '<button class="secundari" onclick="obrirAdmin()">Administració</button>' : ""}
      <button class="secundari" onclick="obrirPerfil()">${sessio.usuari.nom}</button>
      <button class="secundari" onclick="logout()">Surt</button>`;
  } else {
    nav.innerHTML = `
      <button class="secundari" onclick="mostrarVista('vista-login')">Inicia sessió</button>
      <button onclick="mostrarVista('vista-registre')">Registra't</button>`;
  }
}


// ---------- AUTH ----------
async function ferLogin() {
  try {
    const dades = await api("/auth/login", "POST", {
      email: loginEmail.value,
      password: loginPass.value,
    });
    // El token ja s'ha desat a la cookie pel servidor; aquí només guardem l'usuari.
    sessio = { usuari: dades.usuari };
    refrescarNav();
    avis("Sessió iniciada");
    carregarCalendari();
    mostrarVista("vista-calendari");
  } catch (e) { avis(e.message, "err"); }
}

async function ferRegistre() {
  try {
    await api("/auth/register", "POST", {
      nom: regNom.value,
      email: regEmail.value,
      password: regPass.value,
    });
    avis("Compte creat! Ja pots iniciar sessió.");
    mostrarVista("vista-login");
  } catch (e) { avis(e.message, "err"); }
}

async function logout() {
  try { await api("/auth/logout", "POST"); } catch (e) { /* la cookie igual es borra */ }
  sessio = { usuari: null };
  refrescarNav();
  carregarCalendari();
  mostrarVista("vista-calendari");
  avis("Sessió tancada");
}


// ---------- CALENDARIO ----------
async function carregarFiltres() {
  const activitats = await api("/activitats");
  const sel = document.getElementById("filtreActivitat");
  sel.innerHTML = '<option value="">Tots els tipus</option>' +
    activitats.map(a => `<option value="${a.id}">${a.nom}</option>`).join("");
}

async function carregarCalendari() {
  const params = new URLSearchParams();
  if (filtreActivitat.value) params.set("activitat_id", filtreActivitat.value);
  if (filtreData.value) params.set("data", filtreData.value);
  if (filtreMonitor.value) params.set("monitor", filtreMonitor.value);

  const resp = await api("/classes?" + params.toString());
  const cont = document.getElementById("llistaClasses");

  if (!resp.data.length) {
    cont.innerHTML = '<p class="buit">No hi ha classes que coincideixin amb els filtres.</p>';
    return;
  }

  // Agrupamos las clases por día.
  let html = "", diaActual = "";
  for (const c of resp.data) {
    const d = new Date(c.data_hora);
    const dia = d.toLocaleDateString("ca-ES", { weekday: "long", day: "numeric", month: "long" });
    if (dia !== diaActual) { html += `<div class="dia-titol">${dia}</div>`; diaActual = dia; }

    const hora = d.toLocaleTimeString("ca-ES", { hour: "2-digit", minute: "2-digit" });
    const plena = c.places_lliures <= 0;
    html += `
      <div class="targeta">
        <div class="info" onclick="obrirDetall(${c.id})">
          <div><span class="hora">${hora}</span> · ${c.activitat ? c.activitat.nom : "Classe"}</div>
          <div class="meta">${c.monitor} · ${c.sala}</div>
        </div>
        <div>
          ${plena
            ? '<span class="plena">PLENA</span>'
            : `<span class="lliure">${c.places_lliures}/${c.aforament_max}</span>`}
        </div>
      </div>`;
  }
  cont.innerHTML = html;
}


// ---------- DETALLE DE CLASE ----------
async function obrirDetall(id) {
  try {
    const c = await api("/classes/" + id);
    const d = new Date(c.data_hora);
    const data = d.toLocaleDateString("ca-ES", { weekday: "long", day: "numeric", month: "long" });
    const hora = d.toLocaleTimeString("ca-ES", { hour: "2-digit", minute: "2-digit" });
    const plena = c.places_lliures <= 0;

    document.getElementById("detallContingut").innerHTML = `
      <h1>${c.activitat ? c.activitat.nom : "Classe"}</h1>
      <p class="subtitol">${c.activitat ? c.activitat.descripcio : ""}</p>
      <div class="dada"><b>Data i hora</b> ${data}, ${hora}</div>
      <div class="dada"><b>Sala</b> ${c.sala}</div>
      <div class="dada"><b>Monitor</b> ${c.monitor}</div>
      <div class="dada"><b>Places lliures</b> ${c.places_lliures} / ${c.aforament_max}</div>
      <div style="margin-top:20px">
        ${sessio.usuari
          ? (plena
              ? '<button disabled>Classe plena</button>'
              : `<button onclick="reservar(${c.id})">Reserva plaça</button>`)
          : '<button class="secundari" onclick="mostrarVista(\'vista-login\')">Inicia sessió per reservar</button>'}
      </div>`;
    mostrarVista("vista-detall");
  } catch (e) { avis(e.message, "err"); }
}

async function reservar(id) {
  try {
    await api(`/classes/${id}/reserves`, "POST");
    avis("Plaça reservada!");
    obrirDetall(id);   // refresca el detalle con las plazas actualizadas
  } catch (e) { avis(e.message, "err"); }
}


// ---------- PERFIL E HISTORIAL ----------
async function obrirPerfil() {
  try {
    const perfil = await api("/usuaris/me");
    document.getElementById("perfilDades").innerHTML = `
      <div class="dada"><b>Nom</b> ${perfil.nom}</div>
      <div class="dada"><b>Email</b> ${perfil.email}</div>`;
    editNom.value = perfil.nom;
    editPass.value = "";

    const reserves = await api("/usuaris/me/reserves");
    const properes = reserves.data.filter(r => r.estat === "confirmada");
    const historial = reserves.data.filter(r => r.estat !== "confirmada");

    document.getElementById("properes").innerHTML = properes.length
      ? properes.map(r => filaReserva(r, true)).join("")
      : '<p class="buit">No tens cap reserva activa.</p>';

    document.getElementById("historial").innerHTML = historial.length
      ? historial.map(r => filaReserva(r, false)).join("")
      : '<p class="buit">Encara no tens historial.</p>';

    mostrarVista("vista-perfil");
  } catch (e) { avis(e.message, "err"); }
}

function filaReserva(r, cancelable) {
  const d = new Date(r.classe.data_hora);
  const quan = d.toLocaleDateString("ca-ES", { day: "numeric", month: "short" }) + " " +
               d.toLocaleTimeString("ca-ES", { hour: "2-digit", minute: "2-digit" });
  const nom = r.classe.activitat ? r.classe.activitat.nom : "Classe";
  const tag = { confirmada: "tag-confirmada", "cancel·lada": "tag-cancelada", assistida: "tag-assistida" }[r.estat] || "";
  return `
    <div class="fila">
      <div>${quan} · <b>${nom}</b> <span class="estat-tag ${tag}">${r.estat}</span></div>
      ${cancelable ? `<button class="perill petit" onclick="cancelar(${r.classe.id})">Cancel·la</button>` : ""}
    </div>`;
}

async function cancelar(classeId) {
  try {
    await api(`/classes/${classeId}/reserves`, "DELETE");
    avis("Reserva cancel·lada");
    obrirPerfil();
  } catch (e) { avis(e.message, "err"); }
}

async function guardarPerfil() {
  try {
    const cos = { nom: editNom.value };
    if (editPass.value) cos.password = editPass.value;
    const actualitzat = await api("/usuaris/me", "PUT", cos);
    sessio.usuari.nom = actualitzat.nom;
    refrescarNav();
    avis("Perfil actualitzat");
    obrirPerfil();
  } catch (e) { avis(e.message, "err"); }
}


// ---------- ADMIN ----------
async function obrirAdmin() {
  await carregarAdminActivitats();
  await carregarAdminClasses();
  mostrarVista("vista-admin");
}

async function carregarAdminActivitats() {
  const activitats = await api("/activitats");
  document.getElementById("adminActivitats").innerHTML = `
    <table>
      <tr><th>ID</th><th>Nom</th><th>Durada</th><th></th></tr>
      ${activitats.map(a => `
        <tr>
          <td>${a.id}</td><td>${a.nom}</td><td>${a.durada_min} min</td>
          <td><button class="perill petit" onclick="esborrarActivitat(${a.id})">Esborra</button></td>
        </tr>`).join("")}
    </table>`;

  // Rellenamos el desplegable del formulario de nueva clase.
  document.getElementById("novaClasseActivitat").innerHTML =
    activitats.map(a => `<option value="${a.id}">${a.nom}</option>`).join("");
}

async function crearActivitat() {
  try {
    await api("/activitats", "POST", {
      nom: novaActNom.value,
      descripcio: novaActDesc.value,
      durada_min: parseInt(novaActDurada.value) || 60,
    });
    novaActNom.value = ""; novaActDesc.value = ""; novaActDurada.value = "";
    avis("Activitat creada");
    carregarAdminActivitats();
  } catch (e) { avis(e.message, "err"); }
}

async function esborrarActivitat(id) {
  try { await api("/activitats/" + id, "DELETE"); avis("Activitat eliminada"); carregarAdminActivitats(); }
  catch (e) { avis(e.message, "err"); }
}

async function carregarAdminClasses() {
  const resp = await api("/classes");
  document.getElementById("adminClasses").innerHTML = `
    <table>
      <tr><th>ID</th><th>Activitat</th><th>Data</th><th>Monitor</th><th>Ocupació</th><th></th></tr>
      ${resp.data.map(c => {
        const d = new Date(c.data_hora).toLocaleString("ca-ES",
          { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
        const ocupats = c.aforament_max - c.places_lliures;
        return `<tr>
          <td>${c.id}</td>
          <td>${c.activitat ? c.activitat.nom : "-"}</td>
          <td>${d}</td><td>${c.monitor}</td>
          <td>${ocupats}/${c.aforament_max}</td>
          <td><button class="perill petit" onclick="esborrarClasse(${c.id})">Esborra</button></td>
        </tr>`;
      }).join("")}
    </table>`;
}

async function crearClasse() {
  try {
    await api("/classes", "POST", {
      activitat_id: parseInt(novaClasseActivitat.value),
      monitor: novaClasseMonitor.value,
      sala: novaClasseSala.value,
      data_hora: novaClasseData.value,    // input datetime-local da ISO 8601
      aforament_max: parseInt(novaClasseAforament.value),
    });
    avis("Classe programada");
    carregarAdminClasses();
  } catch (e) { avis(e.message, "err"); }
}

async function esborrarClasse(id) {
  try { await api("/classes/" + id, "DELETE"); avis("Classe eliminada"); carregarAdminClasses(); }
  catch (e) { avis(e.message, "err"); }
}


// ---------- Arranque ----------
async function comprovarSessio() {
  // Si la cookie encara és vàlida, /usuaris/me ens tornarà l'usuari i seguim
  // amb la sessió iniciada (encara que haguem recarregat la pàgina).
  try {
    const usuari = await api("/usuaris/me");
    sessio = { usuari: usuari };
  } catch (e) {
    sessio = { usuari: null };   // no hi ha sessió o ha caducat
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  await comprovarSessio();
  refrescarNav();
  carregarFiltres();
  carregarCalendari();
});
