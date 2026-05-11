import sys, os, re
# Agrega la carpeta del archivo al path para que Python encuentre los módulos locales
sys.path.insert(0, os.path.dirname(__file__))

import tkinter as tk
from tkinter import ttk
from datetime import datetime

# Módulos propios del sistema Software FJ
from sistema import GestorSistema
from servicios import ReservaSala, AlquilerEquipo, Asesoria
from reserva import EstadoReserva
from excepciones import SoftwareFJError
from logger import log


# PALETA Y FUENTES

# Diccionario con los dos temas de color disponibles: oscuro y claro.
# Cada tema define colores para fondo, paneles, tarjetas, texto, acentos y estados de reserva.
TEMAS = {
    "oscuro": {
        "BG":      "#0d1117", "PANEL":   "#161b22", "CARD":    "#1c2330",
        "BORDER":  "#30363d", "TEXT":    "#e6edf3", "TEXT_DIM":"#8b949e",
        "ACCENT":  "#58a6ff", "ACCENT2": "#3fb950", "WARN":    "#f85149",
        "AMBER":   "#e3b341",
        "NAV_HOV": "#1f2937",
        "ESTADO_TAG": {
            "PENDIENTE":  {"background": "#2d2500", "foreground": "#e3b341"},
            "CONFIRMADA": {"background": "#0d2818", "foreground": "#3fb950"},
            "COMPLETADA": {"background": "#0d1f3c", "foreground": "#58a6ff"},
            "CANCELADA":  {"background": "#2d0d0d", "foreground": "#f85149"},
        },
    },
    "claro": {
        "BG":      "#f6f8fa", "PANEL":   "#eaeef2", "CARD":    "#ffffff",
        "BORDER":  "#d0d7de", "TEXT":    "#1f2328", "TEXT_DIM":"#57606a",
        "ACCENT":  "#0969da", "ACCENT2": "#1a7f37", "WARN":    "#cf222e",
        "AMBER":   "#9a6700",
        "NAV_HOV": "#d0d7de",
        "ESTADO_TAG": {
            "PENDIENTE":  {"background": "#fff8c5", "foreground": "#9a6700"},
            "CONFIRMADA": {"background": "#dafbe1", "foreground": "#1a7f37"},
            "COMPLETADA": {"background": "#ddf4ff", "foreground": "#0969da"},
            "CANCELADA":  {"background": "#ffebe9", "foreground": "#cf222e"},
        },
    },
}

_MODO_ACTUAL = "oscuro"

def _cargar_tema(modo):
    # Carga el tema seleccionado en variables globales para que toda la UI las use
    global BG, PANEL, CARD, BORDER, TEXT, TEXT_DIM
    global ACCENT, ACCENT2, WARN, AMBER, NAV_HOV, ESTADO_TAG, _MODO_ACTUAL
    t = TEMAS[modo]; _MODO_ACTUAL = modo
    BG=t["BG"]; PANEL=t["PANEL"]; CARD=t["CARD"]; BORDER=t["BORDER"]
    TEXT=t["TEXT"]; TEXT_DIM=t["TEXT_DIM"]
    ACCENT=t["ACCENT"]; ACCENT2=t["ACCENT2"]; WARN=t["WARN"]; AMBER=t["AMBER"]
    NAV_HOV=t["NAV_HOV"]; ESTADO_TAG=t["ESTADO_TAG"]

# Aplica el tema oscuro al arrancar
_cargar_tema("oscuro")

# Constantes de fuente usadas en toda la interfaz
F_H1   = ("Segoe UI", 18, "bold")  # Títulos de panel
F_H2   = ("Segoe UI", 13, "bold")  # Subtítulos
F_BODY = ("Segoe UI",  10)         # Texto general
F_SM   = ("Segoe UI",   9)         # Texto pequeño
F_MONO = ("Consolas",  10)         # Texto monoespaciado (no usado visualmente, reservado)

# Expresiones regulares para validar campos de entrada
_RE_ID    = re.compile(r"^[A-Za-z0-9\-]{3,20}$")
_RE_EMAIL = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")
_RE_TEL   = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")

# Funciones de validación individuales; lanzan ValueError si el valor no cumple la regla
def _val_id(v):
    if not _RE_ID.match(v): raise ValueError()

def _val_nombre(v):
    if len(v.strip()) < 3: raise ValueError()

def _val_email(v):
    if not _RE_EMAIL.match(v): raise ValueError()

def _val_tel(v):
    if not _RE_TEL.match(v): raise ValueError()

def _val_precio(v):
    if float(v) <= 0: raise ValueError()

def _val_horas(v):
    if float(v) <= 0: raise ValueError()



class PillButton(tk.Frame):
    """Botón con apariencia de píldora, efecto hover y cursor de mano."""

    def __init__(self, parent, text="", command=None,
                 bg=ACCENT, fg="white", w=130, h=32, font=F_BODY, **kw):
        super().__init__(parent, bg=BG, width=w, height=h, cursor="hand2")
        self.pack_propagate(False)
        self._bg = bg; self._cmd = command
        # Frame interior que recibe el color de fondo real del botón
        self._inner = tk.Frame(self, bg=bg, cursor="hand2")
        self._inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._lbl = tk.Label(self._inner, text=text, font=font, bg=bg, fg=fg, cursor="hand2")
        self._lbl.place(relx=.5, rely=.5, anchor="center")
        # Enlaza los eventos en el frame, el inner y el label para que el hover sea consistente
        for w_ in (self, self._inner, self._lbl):
            w_.bind("<Enter>",    self._enter)
            w_.bind("<Leave>",    self._leave)
            w_.bind("<Button-1>", self._click)

    def _enter(self, _=None):
        # Aclara el color al pasar el mouse por encima
        c = self._lighten(self._bg)
        self._inner.config(bg=c); self._lbl.config(bg=c)

    def _leave(self, _=None):
        # Restaura el color original al salir el mouse
        self._inner.config(bg=self._bg); self._lbl.config(bg=self._bg)

    def _click(self, _=None):
        # Ejecuta la función asignada al hacer clic
        if self._cmd: self._cmd()

    @staticmethod
    def _lighten(h):
        # Suma 25 a cada canal RGB del color hexadecimal para aclararlo
        r = min(255, int(h[1:3],16)+25)
        g = min(255, int(h[3:5],16)+25)
        b = min(255, int(h[5:7],16)+25)
        return f"#{r:02x}{g:02x}{b:02x}"


class StyledEntry(tk.Frame):
    """Campo de texto estilizado con placeholder y validación visual en tiempo real."""

    def __init__(self, parent, placeholder="", width=18, validador=None, **kw):
        super().__init__(parent, bg=BG)
        self._ph = placeholder; self._active = False; self._validador = validador
        # Frame exterior que simula el borde del campo
        self._wrap = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        self._wrap.pack(fill="x")
        inner = tk.Frame(self._wrap, bg=CARD); inner.pack(fill="x")
        self.var = tk.StringVar()
        self._e = tk.Entry(inner, textvariable=self.var, bg=CARD, fg=TEXT_DIM,
                           insertbackground=ACCENT, relief="flat",
                           font=F_BODY, bd=5, width=width, **kw)
        self._e.pack(fill="x")
        if placeholder:
            self._set_ph()
            self._e.bind("<FocusIn>",  self._clear)
            self._e.bind("<FocusOut>", self._restore)
        if validador:
            # Activa la validación visual cada vez que el usuario escribe o sale del campo
            self._e.bind("<KeyRelease>", self._validar_live, add="+")
            self._e.bind("<FocusOut>",   self._validar_live, add="+")

    def set_borde(self, color=BORDER):
        # Cambia el color del borde exterior del campo
        self._wrap.config(bg=color)

    def _validar_live(self, _=None):
        # Pinta el borde verde si el valor es válido, rojo si no
        if self._active or not self._validador: return
        valor = self.var.get().strip()
        if not valor:
            self.set_borde(BORDER); return
        try:
            self._validador(valor); self.set_borde(ACCENT2)
        except:
            self.set_borde(WARN)

    def _set_ph(self):
        # Muestra el placeholder en gris
        self.var.set(self._ph); self._e.config(fg=TEXT_DIM); self._active = True

    def _clear(self, _=None):
        # Borra el placeholder al hacer foco
        if self._active: self.var.set(""); self._e.config(fg=TEXT); self._active = False

    def _restore(self, _=None):
        # Restaura el placeholder si el campo quedó vacío
        if not self.var.get(): self._set_ph()

    def get(self):
        # Devuelve el texto real; cadena vacía si el placeholder está activo
        return "" if self._active else self.var.get().strip()

    def set(self, v):
        # Asigna un valor al campo y desactiva el placeholder
        self.var.set(v); self._e.config(fg=TEXT); self._active = False

    def clear(self):
        # Vacía el campo y restaura el placeholder y el borde por defecto
        self.var.set(""); self._set_ph(); self.set_borde(BORDER)


class StyledCombo(tk.Frame):
    """Combobox (lista desplegable) estilizado con borde simulado."""

    def __init__(self, parent, values=None, width=17, **kw):
        super().__init__(parent, bg=BG)
        wrap = tk.Frame(self, bg=BORDER, padx=1, pady=1); wrap.pack(fill="x")
        inner = tk.Frame(wrap, bg=CARD); inner.pack(fill="x")
        self.var = tk.StringVar()
        self._cb = ttk.Combobox(inner, textvariable=self.var, values=values or [],
                                state="readonly", font=F_BODY, width=width, **kw)
        self._cb.pack(fill="x")

    def get(self): return self.var.get()
    def set(self, v): self.var.set(v)
    def set_values(self, vals): self._cb.configure(values=vals); self.var.set("")
    def bind_select(self, fn): self._cb.bind("<<ComboboxSelected>>", fn)


def lbl(parent, text, font=F_SM, fg=None, bg=None, **kw):
    """Crea y devuelve un Label con los colores del tema aplicados por defecto."""
    return tk.Label(parent, text=text, font=font,
                    fg=fg if fg is not None else TEXT_DIM,
                    bg=bg if bg is not None else CARD, **kw)


def separador(parent, bg=CARD):
    """Inserta una línea horizontal de 1px como separador visual."""
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(6,10))


def mini_chart(n, maximo=8):
    """Devuelve una barra de texto Unicode proporcional al valor n sobre el máximo."""
    filled = min(n, maximo)
    return "█" * filled + "░" * (maximo - filled) + f"  {n}"



def toast(root, msg, error=False):
    """Muestra una notificación flotante temporal en la parte inferior de la ventana.
    Verde para éxito, rojo para error. Se destruye automáticamente a los 3.2 segundos."""
    color = WARN if error else ACCENT2
    t = tk.Toplevel(root)
    t.overrideredirect(True); t.attributes("-topmost", True)
    frm = tk.Frame(t, bg=color, padx=18, pady=10); frm.pack()
    tk.Label(frm, text=msg, font=F_BODY, bg=color, fg="white", wraplength=420).pack()
    t.update_idletasks()
    # Centra el toast horizontalmente en la ventana principal
    rx = root.winfo_x() + root.winfo_width()//2
    ry = root.winfo_y() + root.winfo_height() - 80
    t.geometry(f"+{rx - t.winfo_width()//2}+{ry}")
    t.after(3200, lambda: t.destroy() if t.winfo_exists() else None)



class ConfirmarDialog(tk.Toplevel):
    """Ventana modal de confirmación con botones 'Cancelar' y 'Sí, confirmar'.
    Bloquea la ventana principal hasta que el usuario responda."""

    def __init__(self, root, titulo, mensaje, color_btn=None):
        super().__init__(root)
        self.title("")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.attributes("-topmost", True)
        self.grab_set()  # Bloquea interacción con la ventana padre
        self._resultado = False

        w, h = 360, 180
        rx = root.winfo_x() + root.winfo_width()//2  - w//2
        ry = root.winfo_y() + root.winfo_height()//2 - h//2
        self.geometry(f"{w}x{h}+{rx}+{ry}")

        color_acento = color_btn or WARN
        tk.Frame(self, bg=color_acento, height=3).pack(fill="x")  # Franja de color superior

        body = tk.Frame(self, bg=BG, padx=28, pady=20); body.pack(fill="both", expand=True)

        tk.Label(body, text=titulo, font=("Segoe UI",11,"bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(body, text=mensaje, font=F_SM,
                 bg=BG, fg=TEXT_DIM, wraplength=300, justify="left").pack(anchor="w", pady=(6,20))

        btns = tk.Frame(body, bg=BG); btns.pack(anchor="e")
        PillButton(btns, "Cancelar", self._no,
                   bg=BORDER, fg=TEXT_DIM, w=100, h=30, font=F_SM).pack(side="left", padx=(0,8))
        PillButton(btns, "Sí, confirmar", self._si,
                   bg=color_acento, w=120, h=30, font=F_SM).pack(side="left")

        # Atajos de teclado: Enter confirma, Escape cancela
        self.bind("<Return>", lambda _: self._si())
        self.bind("<Escape>", lambda _: self._no())
        self.wait_window()  # Espera hasta que la ventana se cierre

    def _si(self):  self._resultado = True;  self.destroy()
    def _no(self):  self._resultado = False; self.destroy()

    @property
    def confirmado(self): return self._resultado  # True si el usuario confirmó


class Tooltip:
    """Muestra un recuadro emergente con información detallada al pasar el mouse
    sobre una fila del Treeview."""

    def __init__(self, tree, fn_info):
        self._tree  = tree
        self._fn    = fn_info   # Función que recibe el ID de la fila y devuelve un dict de datos
        self._win   = None      # Referencia a la ventana del tooltip activo
        self._fila  = None      # ID de la última fila detectada
        tree.bind("<Motion>", self._on_motion, add="+")
        tree.bind("<Leave>",  self._ocultar,   add="+")

    def _on_motion(self, event):
        # Detecta sobre qué fila está el cursor y mueve o recrea el tooltip
        fila = self._tree.identify_row(event.y)
        if fila == self._fila:
            if self._win and self._win.winfo_exists():
                x = self._tree.winfo_rootx() + event.x + 18
                y = self._tree.winfo_rooty() + event.y + 10
                self._win.geometry(f"+{x}+{y}")
            return
        self._ocultar()
        self._fila = fila
        if not fila: return
        vals = self._tree.item(fila, "values")
        if not vals: return
        info = self._fn(str(vals[0]))  # Obtiene los datos usando el primer valor (ID) de la fila
        if not info: return
        self._mostrar(event, info)

    def _mostrar(self, event, info):
        # Crea la ventana del tooltip con cada clave y valor del dict
        x = self._tree.winfo_rootx() + event.x + 18
        y = self._tree.winfo_rooty() + event.y + 10
        self._win = tk.Toplevel(self._tree)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        borde = tk.Frame(self._win, bg=ACCENT, padx=1, pady=1); borde.pack()
        body  = tk.Frame(borde, bg=PANEL, padx=14, pady=10); body.pack()
        for k, v in info.items():
            f = tk.Frame(body, bg=PANEL); f.pack(fill="x", pady=1)
            tk.Label(f, text=f"{k}:", font=("Segoe UI",8),
                     bg=PANEL, fg=TEXT_DIM, width=13, anchor="w").pack(side="left")
            tk.Label(f, text=str(v), font=("Segoe UI",8,"bold"),
                     bg=PANEL, fg=TEXT, anchor="w").pack(side="left")
        self._win.geometry(f"+{x}+{y}")

    def _ocultar(self, _=None):
        # Destruye el tooltip actual y resetea el estado
        self._fila = None
        if self._win:
            try: self._win.destroy()
            except: pass
            self._win = None


class VentanaDetalle(tk.Toplevel):
    """Ventana secundaria que muestra el detalle completo de un registro
    (cliente, servicio o reserva) y opcionalmente botones de acción."""

    def __init__(self, root, titulo, info, acciones=None):
        super().__init__(root)
        self.title(titulo)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        # Altura dinámica según la cantidad de campos y acciones
        alto = 130 + len(info) * 30 + len(acciones or []) * 46
        w, h = 430, min(alto, 560)
        rx = root.winfo_x() + root.winfo_width()//2  - w//2
        ry = root.winfo_y() + root.winfo_height()//2 - h//2
        self.geometry(f"{w}x{h}+{rx}+{ry}")

        tk.Label(self, text=titulo, font=F_H2, bg=BG, fg=ACCENT).pack(padx=24, pady=(20,6), anchor="w")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=24)

        cw = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        cw.pack(fill="x", padx=24, pady=12)
        card = tk.Frame(cw, bg=CARD, padx=20, pady=14); card.pack(fill="x")

        # Muestra cada par clave-valor del dict info en una fila separada
        for clave, valor in info.items():
            f = tk.Frame(card, bg=CARD); f.pack(fill="x", pady=2)
            tk.Label(f, text=clave, font=("Segoe UI",9),
                     bg=CARD, fg=TEXT_DIM, width=16, anchor="w").pack(side="left")
            tk.Label(f, text=str(valor), font=("Segoe UI",9,"bold"),
                     bg=CARD, fg=TEXT, anchor="w", wraplength=220).pack(side="left")

        if acciones:
            af = tk.Frame(self, bg=BG); af.pack(fill="x", padx=24, pady=(0,6))
            for texto, fn, color in acciones:
                def hacer(f=fn):
                    # Ejecuta la acción y muestra un toast si hay error
                    try: f()
                    except SoftwareFJError as ex:
                        toast(root, str(ex), error=True)
                    self.destroy()
                PillButton(af, texto, hacer, bg=color, w=130, h=30, font=F_SM).pack(side="left", padx=(0,8))

        PillButton(self, "✕  Cerrar", self.destroy, bg="#444c56", w=100, h=28, font=F_SM).pack(pady=(4,16))


def hacer_tabla(parent, titulo, cols, anchos, altura=14, fn_tooltip=None):
    """Construye un Treeview estilizado con cabecera, barra de búsqueda y scrollbar.
    Devuelve (tree, badge, lbl_vacio, var_busqueda)."""

    # Cabecera con título y contador (badge) de registros visibles
    cabecera = tk.Frame(parent, bg=CARD)
    cabecera.pack(fill="x", padx=16, pady=(14,4))
    tk.Label(cabecera, text=titulo, font=("Segoe UI",10,"bold"),
             fg=ACCENT, bg=CARD).pack(side="left")
    lbl_badge = tk.Label(cabecera, text="0", font=("Segoe UI",8,"bold"),
                         bg=ACCENT, fg="white", padx=7, pady=1)
    lbl_badge.pack(side="left", padx=(8,0))

    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12)

    # Barra de búsqueda en tiempo real
    barra = tk.Frame(parent, bg=CARD); barra.pack(fill="x", padx=12, pady=(8,2))
    tk.Label(barra, text="🔍", bg=CARD, fg=TEXT_DIM, font=F_SM).pack(side="left", padx=(0,4))
    var_busqueda = tk.StringVar()
    tk.Entry(barra, textvariable=var_busqueda, bg=PANEL, fg=TEXT,
             insertbackground=ACCENT, relief="flat",
             font=F_SM, bd=4).pack(side="left", fill="x", expand=True)

    # Estilo personalizado para el Treeview
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("FJ.Treeview", background=CARD, foreground=TEXT,
                    fieldbackground=CARD, rowheight=28, font=F_BODY, borderwidth=0)
    style.configure("FJ.Treeview.Heading", background=PANEL, foreground=TEXT_DIM,
                    font=("Segoe UI",9,"bold"), relief="flat")
    style.map("FJ.Treeview", background=[("selected","#2d3748")])

    ct = tk.Frame(parent, bg=CARD); ct.pack(fill="both", expand=True)
    tree = ttk.Treeview(ct, columns=cols, show="headings",
                        style="FJ.Treeview", height=altura)
    for c, w in zip(cols, anchos):
        tree.heading(c, text=c); tree.column(c, width=w, anchor="w")

    tree.tag_configure("hover", background="#252e3f")
    _ul = [None]  # Lista de un elemento usada como referencia mutable a la última fila hover

    def _mot(event):
        # Aplica el tag hover a la fila bajo el cursor
        f = tree.identify_row(event.y)
        if f == _ul[0]: return
        if _ul[0]:
            tree.item(_ul[0], tags=[t for t in tree.item(_ul[0],"tags") if t != "hover"])
        if f:
            tree.item(f, tags=list(tree.item(f,"tags")) + ["hover"])
        _ul[0] = f

    def _lv(event):
        # Quita el hover cuando el mouse sale del Treeview
        if _ul[0]:
            tree.item(_ul[0], tags=[t for t in tree.item(_ul[0],"tags") if t != "hover"])
        _ul[0] = None

    tree.bind("<Motion>", _mot)
    tree.bind("<Leave>",  _lv)

    # Scrollbar vertical vinculada al Treeview
    sb = ttk.Scrollbar(ct, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True, padx=(12,0), pady=8)
    sb.pack(side="right", fill="y", pady=8)

    # Etiqueta que aparece cuando no hay registros
    lbl_vacio = tk.Label(parent, text="Sin registros aún",
                         font=("Segoe UI",10,"italic"), bg=CARD, fg=TEXT_DIM)

    if fn_tooltip:
        Tooltip(tree, fn_tooltip)

    return tree, lbl_badge, lbl_vacio, var_busqueda


def sync_badge(tree, badge, vacio):
    """Actualiza el contador del badge y muestra u oculta el mensaje de 'Sin registros'."""
    n = len(tree.get_children())
    badge.config(text=str(n))
    if n == 0: vacio.pack(pady=20)
    else:      vacio.pack_forget()


class PanelClientes(tk.Frame):
    """Panel de la pestaña Clientes: formulario de registro a la izquierda
    y tabla de clientes registrados a la derecha."""

    def __init__(self, parent, gestor: GestorSistema, root):
        super().__init__(parent, bg=BG)
        self.gestor = gestor; self.root = root
        self._datos = []  # Lista local con los datos cargados del gestor
        self._construir()

    def _info_tooltip(self, id_val):
        """Devuelve un dict con los datos del cliente para el tooltip."""
        try:
            c = self.gestor.obtener_cliente(id_val)
            n_reservas = len(self.gestor.listar_reservas(id_cliente=id_val))
            return {
                "ID":         c.identificacion,
                "Nombre":     c.nombre,
                "Email":      c.email,
                "Teléfono":   c.telefono,
                "Empresa":    c.empresa or "—",
                "Estado":     "Activo" if c.activo else "Inactivo",
                "Reservas":   n_reservas,
                "Creado":     c.fecha_creacion_str,
            }
        except: return None

    def _abrir_detalle(self, event):
        """Abre VentanaDetalle al hacer doble clic sobre una fila del Treeview."""
        sel = self.tree.selection()
        if not sel: return
        id_val = str(self.tree.item(sel[0])["values"][0])
        info = self._info_tooltip(id_val)
        if not info: return
        try:
            c = self.gestor.obtener_cliente(id_val)
            acciones = []
            if c.activo:
                # Solo muestra el botón de desactivar si el cliente está activo
                acciones.append(("⊘ Desactivar",
                                 lambda: (self.gestor.desactivar_cliente(id_val), self._refrescar()),
                                 WARN))
            VentanaDetalle(self.root, f"Cliente — {id_val}", info, acciones)
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _construir(self):
        """Construye todos los widgets del panel."""
        tk.Label(self, text="👤  Clientes", font=F_H1, bg=BG, fg=TEXT).pack(anchor="w", padx=30, pady=(24,4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(0,18))

        cont = tk.Frame(self, bg=BG); cont.pack(fill="both", expand=True, padx=30)
        cont.columnconfigure(0, weight=1); cont.columnconfigure(1, weight=2)

        fw = tk.Frame(cont, bg=BORDER, padx=1, pady=1)
        fw.grid(row=0, column=0, sticky="n", padx=(0,16))
        form = tk.Frame(fw, bg=CARD, padx=20, pady=20); form.pack()

        lbl(form, "REGISTRAR CLIENTE", font=("Segoe UI",10,"bold"), fg=ACCENT).pack(anchor="w")
        separador(form)

        # Crea un StyledEntry por cada campo con su placeholder y validador
        self.entries = {}
        campos_val = [
            ("Identificación",  "CC-001",            _val_id),
            ("Nombre completo", "Ana García",         _val_nombre),
            ("Email",           "ana@email.com",      _val_email),
            ("Teléfono",        "+57 300 000 0000",   _val_tel),
            ("Empresa",         "Opcional",           None),
        ]
        for etiqueta, ph, val in campos_val:
            lbl(form, etiqueta).pack(anchor="w", pady=(6,2))
            e = StyledEntry(form, placeholder=ph, width=26, validador=val)
            e.pack(fill="x")
            self.entries[etiqueta] = e

        fila_btn = tk.Frame(form, bg=CARD); fila_btn.pack(fill="x", pady=(16,0))
        PillButton(fila_btn, "✓  Registrar", self._registrar, bg=ACCENT2, w=150).pack(side="left", padx=(0,8))
        PillButton(fila_btn, "✕  Limpiar",   self._limpiar,   bg="#444c56", w=110).pack(side="left")

        lw = tk.Frame(cont, bg=BORDER, padx=1, pady=1)
        lw.grid(row=0, column=1, sticky="nsew")
        li = tk.Frame(lw, bg=CARD); li.pack(fill="both", expand=True)

        cols   = ("ID","Nombre","Email","Estado","Historial")
        anchos = (90,150,170,70,110)
        self.tree, self._badge, self._vacio, self._busq = \
            hacer_tabla(li, "CLIENTES REGISTRADOS", cols, anchos,
                        fn_tooltip=self._info_tooltip)

        # Actualiza el filtro de búsqueda cada vez que el usuario escribe
        self._busq.trace_add("write", lambda *_: self._filtrar())
        # Un clic copia el ID al portapapeles; doble clic abre el detalle
        self.tree.bind("<ButtonRelease-1>", self._copiar_id)
        self.tree.bind("<Double-1>",        self._abrir_detalle)

        bf = tk.Frame(li, bg=CARD); bf.pack(fill="x", padx=12, pady=(0,12))
        PillButton(bf, "⊘  Desactivar seleccionado", self._desactivar, bg=WARN, w=220, h=30).pack(side="left")

        self._refrescar()

    def _registrar(self):
        """Lee los campos del formulario y llama al gestor para registrar el cliente."""
        e = self.entries
        try:
            self.gestor.registrar_cliente(
                e["Identificación"].get(), e["Nombre completo"].get(),
                e["Email"].get(), e["Teléfono"].get(), e["Empresa"].get(),
            )
            toast(self.root, "✓ Cliente registrado exitosamente")
            self._limpiar(); self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _limpiar(self):
        """Resetea todos los campos del formulario a sus placeholders."""
        for e in self.entries.values(): e.clear()

    def _desactivar(self):
        """Desactiva el cliente seleccionado en la tabla."""
        sel = self.tree.selection()
        if not sel: toast(self.root, "Selecciona un cliente primero", error=True); return
        ident = self.tree.item(sel[0])["values"][0]
        try:
            self.gestor.desactivar_cliente(str(ident))
            toast(self.root, f"Cliente '{ident}' desactivado")
            self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _copiar_id(self, event):
        """Copia el ID de la fila seleccionada al portapapeles del sistema."""
        sel = self.tree.selection()
        if not sel: return
        id_val = str(self.tree.item(sel[0])["values"][0])
        self.root.clipboard_clear(); self.root.clipboard_append(id_val)
        toast(self.root, f"📋 ID '{id_val}' copiado al portapapeles")

    def _refrescar(self):
        """Recarga los datos del gestor en la lista interna y actualiza el filtro."""
        self._datos = []
        for c in self.gestor.listar_clientes():
            n = len(self.gestor.listar_reservas(id_cliente=c.identificacion))
            self._datos.append((
                c.identificacion, c.nombre, c.email,
                "Activo" if c.activo else "Inactivo",
                mini_chart(n),  # Barra visual de cantidad de reservas
            ))
        self._filtrar()

    def _filtrar(self):
        """Filtra las filas visibles en el Treeview según el texto de búsqueda."""
        termino = self._busq.get().lower().strip()
        self.tree.delete(*self.tree.get_children())
        for fila in self._datos:
            if termino and not any(termino in str(v).lower() for v in fila): continue
            self.tree.insert("", "end", values=fila)
        sync_badge(self.tree, self._badge, self._vacio)


class PanelServicios(tk.Frame):
    """Panel de la pestaña Servicios: formulario de creación a la izquierda
    y tabla de servicios registrados a la derecha."""

    def __init__(self, parent, gestor: GestorSistema, root):
        super().__init__(parent, bg=BG)
        self.gestor = gestor; self.root = root
        self._datos = []
        self._construir()

    def _info_tooltip(self, id_val):
        """Devuelve un dict con los datos del servicio para el tooltip."""
        try:
            s = self.gestor.obtener_servicio(id_val)
            info = {
                "ID":          s.id_entidad,
                "Nombre":      s.nombre,
                "Precio/hora": f"${s.precio_hora:,.0f}",
                "Tipo":        type(s).__name__.replace("Reserva","Sala").replace("Alquiler","Alquiler"),
                "Disponible":  "Sí" if s.disponible else "No",
            }
            # Agrega campos específicos según el tipo concreto de servicio
            if isinstance(s, ReservaSala):
                info["Capacidad"]  = f"{s.capacidad_max} personas"
                info["Proyector"]  = "Sí" if s.tiene_proyector else "No"
            elif isinstance(s, AlquilerEquipo):
                info["Equipo"]     = s.tipo_equipo
                info["Stock"]      = s.stock_disponible
            elif isinstance(s, Asesoria):
                info["Especialidad"] = s.especialidad
                info["Nivel"]        = s.nivel
            return info
        except: return None

    def _abrir_detalle(self, event):
        """Abre VentanaDetalle al hacer doble clic sobre una fila."""
        sel = self.tree.selection()
        if not sel: return
        id_val = str(self.tree.item(sel[0])["values"][0])
        info = self._info_tooltip(id_val)
        if not info: return
        VentanaDetalle(self.root, f"Servicio — {id_val}", info)

    def _construir(self):
        """Construye todos los widgets del panel."""
        tk.Label(self, text="🛠️  Servicios", font=F_H1, bg=BG, fg=TEXT).pack(anchor="w", padx=30, pady=(24,4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(0,18))

        cont = tk.Frame(self, bg=BG); cont.pack(fill="both", expand=True, padx=30)
        cont.columnconfigure(0, weight=1); cont.columnconfigure(1, weight=2)

        fw = tk.Frame(cont, bg=BORDER, padx=1, pady=1)
        fw.grid(row=0, column=0, sticky="n", padx=(0,16))
        self.form = tk.Frame(fw, bg=CARD, padx=20, pady=20); self.form.pack()

        lbl(self.form, "CREAR SERVICIO", font=("Segoe UI",10,"bold"), fg=ACCENT).pack(anchor="w")
        separador(self.form)

        lbl(self.form, "Tipo de servicio").pack(anchor="w", pady=(4,2))
        self.combo_tipo = StyledCombo(self.form,
            values=["Sala de reuniones","Alquiler de equipo","Asesoría especializada"], width=26)
        self.combo_tipo.pack(fill="x")
        # Al cambiar el tipo, se muestran los campos específicos del servicio seleccionado
        self.combo_tipo.bind_select(self._cambiar_tipo)

        lbl(self.form, "ID del servicio").pack(anchor="w", pady=(10,2))
        self.e_id = StyledEntry(self.form, "SALA-01", width=26, validador=_val_id)
        self.e_id.pack(fill="x")

        lbl(self.form, "Nombre").pack(anchor="w", pady=(8,2))
        self.e_nombre = StyledEntry(self.form, "Sala Ejecutiva A", width=26, validador=_val_nombre)
        self.e_nombre.pack(fill="x")

        lbl(self.form, "Precio por hora ($)").pack(anchor="w", pady=(8,2))
        self.e_precio = StyledEntry(self.form, "80000", width=26, validador=_val_precio)
        self.e_precio.pack(fill="x")

        # Contenedor dinámico donde se insertan los campos extras según el tipo
        self.frame_extra = tk.Frame(self.form, bg=CARD); self.frame_extra.pack(fill="x")
        self._campos_extra = {}
        self._mostrar_campos_sala()  # Sala es el tipo por defecto

        fila_btn = tk.Frame(self.form, bg=CARD); fila_btn.pack(fill="x", pady=(16,0))
        PillButton(fila_btn, "✓  Crear servicio", self._crear, bg=ACCENT2, w=160).pack(side="left", padx=(0,8))
        PillButton(fila_btn, "✕  Limpiar", self._limpiar, bg="#444c56", w=100).pack(side="left")

        lw = tk.Frame(cont, bg=BORDER, padx=1, pady=1)
        lw.grid(row=0, column=1, sticky="nsew")
        li = tk.Frame(lw, bg=CARD); li.pack(fill="both", expand=True)

        cols   = ("ID","Tipo","Nombre","Precio/h","Disponible")
        anchos = (90,120,200,100,80)
        self.tree, self._badge, self._vacio, self._busq = \
            hacer_tabla(li, "SERVICIOS REGISTRADOS", cols, anchos,
                        fn_tooltip=self._info_tooltip)

        self._busq.trace_add("write", lambda *_: self._filtrar())
        self.tree.bind("<ButtonRelease-1>", self._copiar_id)
        self.tree.bind("<Double-1>",        self._abrir_detalle)
        self._refrescar()

    def _limpiar_extra(self):
        """Elimina los widgets del área de campos extras."""
        for w in self.frame_extra.winfo_children(): w.destroy()
        self._campos_extra = {}

    def _mostrar_campos_sala(self):
        """Muestra los campos específicos para Sala de reuniones."""
        self._limpiar_extra()
        lbl(self.frame_extra, "Capacidad máxima (personas)").pack(anchor="w", pady=(8,2))
        e = StyledEntry(self.frame_extra, "10", width=26); e.pack(fill="x")
        self._campos_extra["capacidad"] = e
        lbl(self.frame_extra, "¿Tiene proyector?").pack(anchor="w", pady=(8,2))
        self._proyector_var = tk.BooleanVar()
        fila = tk.Frame(self.frame_extra, bg=CARD); fila.pack(anchor="w")
        tk.Radiobutton(fila, text="Sí", variable=self._proyector_var, value=True,
                       bg=CARD, fg=TEXT, selectcolor=CARD, font=F_BODY, activebackground=CARD).pack(side="left")
        tk.Radiobutton(fila, text="No", variable=self._proyector_var, value=False,
                       bg=CARD, fg=TEXT, selectcolor=CARD, font=F_BODY, activebackground=CARD).pack(side="left", padx=12)

    def _mostrar_campos_equipo(self):
        """Muestra los campos específicos para Alquiler de equipo."""
        self._limpiar_extra()
        lbl(self.frame_extra, "Tipo / descripción del equipo").pack(anchor="w", pady=(8,2))
        e = StyledEntry(self.frame_extra, "Laptop 16GB RAM", width=26); e.pack(fill="x")
        self._campos_extra["tipo"] = e
        lbl(self.frame_extra, "Stock disponible (unidades)").pack(anchor="w", pady=(8,2))
        e2 = StyledEntry(self.frame_extra, "3", width=26); e2.pack(fill="x")
        self._campos_extra["stock"] = e2

    def _mostrar_campos_asesoria(self):
        """Muestra los campos específicos para Asesoría especializada."""
        self._limpiar_extra()
        lbl(self.frame_extra, "Especialidad").pack(anchor="w", pady=(8,2))
        e = StyledEntry(self.frame_extra, "Derecho Corporativo", width=26); e.pack(fill="x")
        self._campos_extra["especialidad"] = e
        lbl(self.frame_extra, "Nivel").pack(anchor="w", pady=(8,2))
        c = StyledCombo(self.frame_extra, values=["basico","intermedio","experto"], width=26)
        c.pack(fill="x"); c.set("basico")
        self._campos_extra["nivel"] = c

    def _cambiar_tipo(self, _=None):
        """Actualiza el área de campos extras según el tipo de servicio seleccionado."""
        tipo = self.combo_tipo.get()
        if "Sala" in tipo:     self._mostrar_campos_sala()
        elif "equipo" in tipo: self._mostrar_campos_equipo()
        elif "Asesor" in tipo: self._mostrar_campos_asesoria()

    def _crear(self):
        """Lee los campos del formulario, construye el servicio correspondiente
        y lo registra en el gestor."""
        tipo = self.combo_tipo.get(); id_s = self.e_id.get(); nombre = self.e_nombre.get()
        try:
            precio = float(self.e_precio.get())
        except ValueError:
            toast(self.root, "El precio debe ser un número", error=True); return
        try:
            if "Sala" in tipo:
                svc = ReservaSala(id_s, nombre, precio,
                                  int(self._campos_extra["capacidad"].get()),
                                  self._proyector_var.get())
            elif "equipo" in tipo:
                svc = AlquilerEquipo(id_s, nombre, precio,
                                     self._campos_extra["tipo"].get(),
                                     int(self._campos_extra["stock"].get()))
            elif "Asesor" in tipo:
                svc = Asesoria(id_s, nombre, precio,
                               self._campos_extra["especialidad"].get(),
                               self._campos_extra["nivel"].get() or "basico")
            else:
                toast(self.root, "Selecciona un tipo de servicio", error=True); return
            self.gestor.registrar_servicio(svc)
            toast(self.root, f"✓ Servicio '{nombre}' registrado")
            self._limpiar(); self._refrescar()
        except (SoftwareFJError, ValueError) as ex:
            toast(self.root, str(ex), error=True)

    def _limpiar(self):
        """Limpia los campos comunes del formulario."""
        self.e_id.clear(); self.e_nombre.clear(); self.e_precio.clear()

    def _copiar_id(self, event):
        """Copia el ID del servicio seleccionado al portapapeles."""
        sel = self.tree.selection()
        if not sel: return
        id_val = str(self.tree.item(sel[0])["values"][0])
        self.root.clipboard_clear(); self.root.clipboard_append(id_val)
        toast(self.root, f"📋 ID '{id_val}' copiado al portapapeles")

    def _refrescar(self):
        """Recarga los servicios del gestor en la lista interna."""
        self._datos = []
        for s in self.gestor.listar_servicios():
            tipo = type(s).__name__.replace("Reserva","Sala").replace("Alquiler","Alq.")
            disp = "✓" if s.disponible else "✗"
            self._datos.append((s.id_entidad, tipo, s.nombre, f"${s.precio_hora:,.0f}", disp))
        self._filtrar()

    def _filtrar(self):
        """Filtra las filas del Treeview según el texto de búsqueda."""
        termino = self._busq.get().lower().strip()
        self.tree.delete(*self.tree.get_children())
        for fila in self._datos:
            if termino and not any(termino in str(v).lower() for v in fila): continue
            self.tree.insert("", "end", values=fila)
        sync_badge(self.tree, self._badge, self._vacio)

    def refrescar_publico(self):
        self._refrescar()


class PanelReservas(tk.Frame):
    """Panel de la pestaña Reservas: formulario de creación a la izquierda
    y tabla de reservas con acciones de confirmación, completado y cancelación."""

    def __init__(self, parent, gestor: GestorSistema, root):
        super().__init__(parent, bg=BG)
        self.gestor = gestor; self.root = root
        self._datos = []
        self._construir()

    def _info_tooltip(self, id_val):
        """Devuelve un dict con los datos de la reserva para el tooltip."""
        try:
            reservas = self.gestor.listar_reservas()
            r = next((r for r in reservas if r.id_reserva == id_val), None)
            if not r: return None
            return {
                "ID":       r.id_reserva,
                "Cliente":  r.cliente.nombre,
                "Servicio": r.servicio.nombre,
                "Horas":    r.horas,
                "Costo":    f"${r.costo:,.0f}",
                "IVA":      "Sí" if getattr(r, '_Reserva__con_iva', True) else "No",
                "Estado":   r.estado.value,
                "Creada":   r.fecha_creacion_str,
                "Notas":    getattr(r, '_Reserva__notas', "") or "—",
            }
        except: return None

    def _abrir_detalle(self, event):
        """Abre VentanaDetalle al hacer doble clic; incluye botones de acción
        según el estado actual de la reserva."""
        sel = self.tree.selection()
        if not sel: return
        id_val = str(self.tree.item(sel[0])["values"][0])
        info = self._info_tooltip(id_val)
        if not info: return

        reservas = self.gestor.listar_reservas()
        r = next((r for r in reservas if r.id_reserva == id_val), None)
        if not r: return

        # Construye la lista de acciones disponibles según el estado de la reserva
        acciones = []
        if r.estado == EstadoReserva.PENDIENTE:
            acciones.append(("✓ Confirmar",
                             lambda: (self.gestor.confirmar_reserva(id_val), self._refrescar()),
                             ACCENT2))
        if r.estado == EstadoReserva.CONFIRMADA:
            acciones.append(("✔ Completar",
                             lambda: (self.gestor.completar_reserva(id_val), self._refrescar()),
                             ACCENT))
        if r.estado not in (EstadoReserva.CANCELADA, EstadoReserva.COMPLETADA):
            acciones.append(("✕ Cancelar",
                             lambda: (self.gestor.cancelar_reserva(id_val, "Cancelada desde detalle"), self._refrescar()),
                             WARN))

        VentanaDetalle(self.root, f"Reserva — {id_val}", info, acciones)

    def _construir(self):
        """Construye todos los widgets del panel."""
        tk.Label(self, text="📋  Reservas", font=F_H1, bg=BG, fg=TEXT).pack(anchor="w", padx=30, pady=(24,4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(0,18))

        cont = tk.Frame(self, bg=BG); cont.pack(fill="both", expand=True, padx=30)
        cont.columnconfigure(0, weight=1); cont.columnconfigure(1, weight=2)

        fw = tk.Frame(cont, bg=BORDER, padx=1, pady=1)
        fw.grid(row=0, column=0, sticky="n", padx=(0,16))
        form = tk.Frame(fw, bg=CARD, padx=20, pady=20); form.pack()

        lbl(form, "NUEVA RESERVA", font=("Segoe UI",10,"bold"), fg=ACCENT).pack(anchor="w")
        separador(form)

        lbl(form, "ID Cliente").pack(anchor="w", pady=(4,2))
        self.e_cliente = StyledEntry(form, "CC-001", width=26, validador=_val_id)
        self.e_cliente.pack(fill="x")

        lbl(form, "ID Servicio").pack(anchor="w", pady=(8,2))
        self.e_servicio = StyledEntry(form, "SALA-A", width=26, validador=_val_id)
        self.e_servicio.pack(fill="x")

        lbl(form, "Duración (horas)").pack(anchor="w", pady=(8,2))
        self.e_horas = StyledEntry(form, "2.0", width=26, validador=_val_horas)
        self.e_horas.pack(fill="x")

        lbl(form, "Descuento (%)").pack(anchor="w", pady=(8,2))
        self.e_desc  = StyledEntry(form, "0", width=26); self.e_desc.pack(fill="x")

        lbl(form, "Notas").pack(anchor="w", pady=(8,2))
        self.e_notas = StyledEntry(form, "Opcional", width=26); self.e_notas.pack(fill="x")

        # Checkbox para aplicar o no el IVA al calcular el costo
        self.iva_var = tk.BooleanVar(value=True)
        fila_iva = tk.Frame(form, bg=CARD); fila_iva.pack(anchor="w", pady=(10,0))
        tk.Checkbutton(fila_iva, text="Aplicar IVA (19%)", variable=self.iva_var,
                       bg=CARD, fg=TEXT, selectcolor=CARD,
                       activebackground=CARD, font=F_BODY).pack(side="left")

        lbl(form, "Parámetros extra (opcional)").pack(anchor="w", pady=(12,4))
        lbl(form, "Personas / Unidades / Nivel", fg="#6a7280").pack(anchor="w", pady=(0,2))
        self.e_extra1 = StyledEntry(form, "ej: 5  ó  basico", width=26)
        self.e_extra1.pack(fill="x")

        # Checkboxes para parámetros opcionales específicos de cada tipo de servicio
        self._check_vars = {
            "usar_proyector":  tk.BooleanVar(),
            "seguro":          tk.BooleanVar(),
            "incluir_informe": tk.BooleanVar(),
        }
        for txt, key in [("🖥 Usar proyector","usar_proyector"),
                         ("🔒 Seguro de equipo (+5%)","seguro"),
                         ("📄 Incluir informe (+$50K)","incluir_informe")]:
            tk.Checkbutton(form, text=txt, variable=self._check_vars[key],
                           bg=CARD, fg=TEXT, selectcolor=CARD,
                           activebackground=CARD, font=F_SM).pack(anchor="w")

        fila_btn = tk.Frame(form, bg=CARD); fila_btn.pack(fill="x", pady=(14,0))
        PillButton(fila_btn, "✓  Crear reserva", self._crear, bg=ACCENT2, w=160).pack(side="left", padx=(0,8))
        PillButton(fila_btn, "✕  Limpiar", self._limpiar, bg="#444c56", w=100).pack(side="left")

        lw = tk.Frame(cont, bg=BORDER, padx=1, pady=1)
        lw.grid(row=0, column=1, sticky="nsew")
        li = tk.Frame(lw, bg=CARD); li.pack(fill="both", expand=True)

        cols   = ("ID","Cliente","Servicio","Horas","Costo","Estado")
        anchos = (110,120,160,55,100,90)
        self.tree, self._badge, self._vacio, self._busq = \
            hacer_tabla(li, "RESERVAS", cols, anchos, altura=10,
                        fn_tooltip=self._info_tooltip)

        # Aplica el color de fondo/texto según el estado de cada reserva
        for estado, cfg in ESTADO_TAG.items():
            self.tree.tag_configure(estado, **cfg)

        self._busq.trace_add("write", lambda *_: self._filtrar())
        self.tree.bind("<ButtonRelease-1>", self._copiar_id)
        self.tree.bind("<Double-1>",        self._abrir_detalle)

        # Botones de acción rápida bajo la tabla
        acc = tk.Frame(li, bg=CARD); acc.pack(fill="x", padx=12, pady=(0,12))
        for txt, cmd, color in [
            ("✓ Confirmar", self._confirmar, ACCENT2),
            ("✔ Completar", self._completar, ACCENT),
            ("✕ Cancelar",  self._cancelar,  WARN),
        ]:
            PillButton(acc, txt, cmd, bg=color, w=110, h=28, font=F_SM).pack(side="left", padx=(0,6))

        self._refrescar()

    def _crear(self):
        """Lee el formulario, interpreta los parámetros extra y crea la reserva en el gestor."""
        try:
            horas    = float(self.e_horas.get())
            desc_pct = float(self.e_desc.get() or "0")
            kwargs   = {}
            extra1   = self.e_extra1.get()
            if extra1:
                try:
                    # Si el valor extra es numérico, se pasa como personas y unidades
                    kwargs["num_personas"]      = int(extra1)
                    kwargs["cantidad_unidades"] = int(extra1)
                except ValueError:
                    # Si no es numérico, se interpreta como nivel de asesoría
                    kwargs["nivel_override"] = extra1
            # Agrega solo los checkboxes marcados como True
            for key, var in self._check_vars.items():
                if var.get(): kwargs[key] = True
            r = self.gestor.crear_reserva(
                self.e_cliente.get(), self.e_servicio.get(), horas,
                con_iva=self.iva_var.get(), descuento=desc_pct/100,
                notas=self.e_notas.get(), **kwargs,
            )
            toast(self.root, f"✓ Reserva {r.id_reserva} creada — ${r.costo:,.0f}")
            self._limpiar(); self._refrescar()
        except (SoftwareFJError, ValueError) as ex:
            toast(self.root, str(ex), error=True)

    def _limpiar(self):
        """Resetea todos los campos del formulario."""
        for e in (self.e_cliente, self.e_servicio, self.e_horas,
                  self.e_desc, self.e_notas, self.e_extra1): e.clear()
        for v in self._check_vars.values(): v.set(False)

    def _id_seleccionado(self):
        """Devuelve el ID de la reserva seleccionada, o None si no hay selección."""
        sel = self.tree.selection()
        if not sel:
            toast(self.root, "Selecciona una reserva primero", error=True)
            return None
        return self.tree.item(sel[0])["values"][0]

    def _copiar_id(self, event):
        """Copia el ID de la reserva seleccionada al portapapeles."""
        sel = self.tree.selection()
        if not sel: return
        id_val = str(self.tree.item(sel[0])["values"][0])
        self.root.clipboard_clear(); self.root.clipboard_append(id_val)
        toast(self.root, f"📋 ID '{id_val}' copiado al portapapeles")

    def _confirmar(self):
        """Confirma la reserva seleccionada en la tabla."""
        id_r = self._id_seleccionado()
        if not id_r: return
        try:
            self.gestor.confirmar_reserva(str(id_r))
            toast(self.root, f"Reserva {id_r} confirmada ✓")
            self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _completar(self):
        """Marca como completada la reserva seleccionada."""
        id_r = self._id_seleccionado()
        if not id_r: return
        try:
            self.gestor.completar_reserva(str(id_r))
            toast(self.root, f"Reserva {id_r} completada ✓")
            self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _cancelar(self):
        """Cancela la reserva seleccionada, previa confirmación del usuario."""
        id_r = self._id_seleccionado()
        if not id_r: return
        dialogo = ConfirmarDialog(
            self.root,
            "¿Cancelar reserva?",
            f"Estás a punto de cancelar la reserva {id_r}.\nEsta acción no se puede deshacer.",
            color_btn=WARN,
        )
        if not dialogo.confirmado: return
        try:
            self.gestor.cancelar_reserva(str(id_r), "Cancelada desde interfaz")
            toast(self.root, f"Reserva {id_r} cancelada")
            self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _refrescar(self):
        """Recarga las reservas del gestor en la lista interna."""
        self._datos = []
        for r in self.gestor.listar_reservas():
            self._datos.append((
                r.id_reserva, r.cliente.nombre[:14],
                r.servicio.nombre[:18], r.horas,
                f"${r.costo:,.0f}", r.estado.value
            ))
        self._filtrar()

    def _filtrar(self):
        """Filtra las reservas visibles y aplica el tag de color según el estado."""
        termino = self._busq.get().lower().strip()
        self.tree.delete(*self.tree.get_children())
        for fila in self._datos:
            if termino and not any(termino in str(v).lower() for v in fila): continue
            self.tree.insert("", "end", values=fila, tags=(fila[5],))  # fila[5] = estado
        sync_badge(self.tree, self._badge, self._vacio)

    def refrescar_publico(self):
        self._refrescar()


class PanelReporte(tk.Frame):
    """Panel de la pestaña Reporte: muestra KPIs, desglose por estado,
    gráfica de barras animada y botón de exportación a .txt."""

    def __init__(self, parent, gestor: GestorSistema, root):
        super().__init__(parent, bg=BG)
        self.gestor = gestor; self.root = root
        self._construir()

    def _construir(self):
        """Crea el contenedor principal y carga el reporte por primera vez."""
        tk.Label(self, text="📊  Reporte General", font=F_H1, bg=BG, fg=TEXT).pack(anchor="w", padx=30, pady=(24,4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(0,20))
        self.contenedor = tk.Frame(self, bg=BG)
        self.contenedor.pack(fill="both", expand=True, padx=30)
        self._refrescar()

    def _refrescar(self):
        """Destruye el contenido anterior y reconstruye el reporte con datos actuales."""
        for w in self.contenedor.winfo_children(): w.destroy()

        clientes  = self.gestor.listar_clientes()
        servicios = self.gestor.listar_servicios()
        reservas  = self.gestor.listar_reservas()

        # Contadores por estado
        confirmadas = sum(1 for r in reservas if r.estado == EstadoReserva.CONFIRMADA)
        completadas = sum(1 for r in reservas if r.estado == EstadoReserva.COMPLETADA)
        canceladas  = sum(1 for r in reservas if r.estado == EstadoReserva.CANCELADA)
        pendientes  = sum(1 for r in reservas if r.estado == EstadoReserva.PENDIENTE)
        # Solo suma ingresos de reservas activas (confirmadas o completadas)
        ingresos    = sum(r.costo for r in reservas
                         if r.estado in (EstadoReserva.CONFIRMADA, EstadoReserva.COMPLETADA))

        # Tarjetas KPI en la parte superior
        kpis = tk.Frame(self.contenedor, bg=BG); kpis.pack(fill="x", pady=(0,16))
        for titulo, valor, color in [
            ("👤 Clientes",  str(len(clientes)),  ACCENT),
            ("🛠️ Servicios", str(len(servicios)), ACCENT2),
            ("📋 Reservas",  str(len(reservas)),  AMBER),
            ("💰 Ingresos",  f"${ingresos:,.0f}", "#c9d1d9"),
        ]:
            card = tk.Frame(kpis, bg=BORDER, padx=1, pady=1)
            card.pack(side="left", expand=True, fill="x", padx=6)
            inner = tk.Frame(card, bg=CARD, padx=20, pady=16); inner.pack(fill="both")
            tk.Label(inner, text=titulo, font=F_SM, bg=CARD, fg=TEXT_DIM).pack(anchor="w")
            tk.Label(inner, text=valor, font=("Segoe UI",22,"bold"), bg=CARD, fg=color).pack(anchor="w")

        # Desglose numérico de reservas por estado
        det_wrap = tk.Frame(self.contenedor, bg=BORDER, padx=1, pady=1)
        det_wrap.pack(fill="x", pady=(0,12))
        det = tk.Frame(det_wrap, bg=CARD, padx=24, pady=16); det.pack(fill="both")

        lbl(det, "DESGLOSE DE RESERVAS", font=("Segoe UI",10,"bold"), fg=ACCENT).pack(anchor="w")
        tk.Frame(det, bg=BORDER, height=1).pack(fill="x", pady=(6,10))

        fila_est = tk.Frame(det, bg=CARD); fila_est.pack(fill="x")
        for estado, cant, color in [
            ("Pendientes",  pendientes,  AMBER),
            ("Confirmadas", confirmadas, ACCENT2),
            ("Completadas", completadas, ACCENT),
            ("Canceladas",  canceladas,  WARN),
        ]:
            bloque = tk.Frame(fila_est, bg=CARD); bloque.pack(side="left", expand=True)
            tk.Label(bloque, text=str(cant), font=("Segoe UI",20,"bold"),
                     bg=CARD, fg=color).pack()
            tk.Label(bloque, text=estado, font=F_SM, bg=CARD, fg=TEXT_DIM).pack()

        # Gráfica de barras horizontal animada
        datos_grafica = [
            ("Pendientes",  pendientes,  AMBER),
            ("Confirmadas", confirmadas, ACCENT2),
            ("Completadas", completadas, ACCENT),
            ("Canceladas",  canceladas,  WARN),
        ]
        self._dibujar_grafica(self.contenedor, datos_grafica)

        # Botones de actualización y exportación
        fila_btns = tk.Frame(self.contenedor, bg=BG); fila_btns.pack(pady=(8,0))
        PillButton(fila_btns, "↻  Actualizar", self._refrescar, bg="#444c56", w=150).pack(side="left", padx=(0,10))
        PillButton(fila_btns, "📄  Exportar .txt", self._exportar, bg=ACCENT, w=160).pack(side="left")

    def _dibujar_grafica(self, parent, datos):
        """Dibuja una gráfica de barras horizontales con animación de aparición."""
        if not any(v for _, v, _ in datos): return
        maximo = max(v for _, v, _ in datos) or 1

        cw = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        cw.pack(fill="x", pady=(0,12))
        inner = tk.Frame(cw, bg=CARD, padx=20, pady=16); inner.pack(fill="x")

        lbl(inner, "GRÁFICA DE RESERVAS POR ESTADO",
            font=("Segoe UI",10,"bold"), fg=ACCENT).pack(anchor="w")
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(6,10))

        canvas = tk.Canvas(inner, bg=CARD, height=len(datos)*42+8, highlightthickness=0)
        canvas.pack(fill="x")
        canvas.update_idletasks()

        def animar(prog):
            # Redibuja cada barra con un ancho proporcional a prog (de 0.0 a 1.0)
            canvas.delete("all")
            cw_px = canvas.winfo_width()
            if cw_px < 20: cw_px = 440
            lbl_w, num_w, barra_w = 90, 40, cw_px - 90 - 40 - 16

            for i, (label, valor, color) in enumerate(datos):
                y = i * 42 + 6
                h = 26
                ancho = int(barra_w * (valor / maximo) * prog)
                # Fondo de la barra
                canvas.create_rectangle(lbl_w, y, lbl_w + barra_w, y + h,
                                        fill="#1e2736", outline="")
                # Barra coloreada proporcional al valor
                if ancho > 0:
                    canvas.create_rectangle(lbl_w, y, lbl_w + ancho, y + h,
                                            fill=color, outline="")
                canvas.create_text(lbl_w - 8, y + h//2, text=label,
                                   fill=TEXT_DIM, font=("Segoe UI",9), anchor="e")
                canvas.create_text(lbl_w + barra_w + 6, y + h//2, text=str(valor),
                                   fill=color, font=("Segoe UI",9,"bold"), anchor="w")

            if prog < 1.0:
                inner.after(14, lambda: animar(min(prog + 0.07, 1.0)))

        canvas.after(180, lambda: animar(0.0))

    def _exportar(self):
        """Genera un archivo .txt con el reporte completo en la misma carpeta del script."""
        try:
            clientes  = self.gestor.listar_clientes()
            servicios = self.gestor.listar_servicios()
            reservas  = self.gestor.listar_reservas()

            confirmadas = sum(1 for r in reservas if r.estado == EstadoReserva.CONFIRMADA)
            completadas = sum(1 for r in reservas if r.estado == EstadoReserva.COMPLETADA)
            canceladas  = sum(1 for r in reservas if r.estado == EstadoReserva.CANCELADA)
            pendientes  = sum(1 for r in reservas if r.estado == EstadoReserva.PENDIENTE)
            ingresos    = sum(r.costo for r in reservas
                             if r.estado in (EstadoReserva.CONFIRMADA, EstadoReserva.COMPLETADA))

            ahora    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            nombre   = f"reporte_softwarefj_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            ruta     = os.path.join(os.path.dirname(__file__), nombre)

            lineas = [
                "=" * 58,
                "  REPORTE — SOFTWARE FJ",
                f"  Generado: {ahora}",
                "=" * 58,
                "",
                "RESUMEN",
                f"  Clientes registrados : {len(clientes)}",
                f"  Servicios activos    : {len(servicios)}",
                f"  Total reservas       : {len(reservas)}",
                f"  Ingresos proyectados : ${ingresos:,.0f}",
                "",
                "DESGLOSE RESERVAS",
                f"  Pendientes  : {pendientes}",
                f"  Confirmadas : {confirmadas}",
                f"  Completadas : {completadas}",
                f"  Canceladas  : {canceladas}",
                "",
                "CLIENTES",
            ]
            for c in clientes:
                estado = "Activo" if c.activo else "Inactivo"
                lineas.append(f"  [{c.identificacion}] {c.nombre} | {c.email} | {estado}")

            lineas += ["", "SERVICIOS"]
            for s in servicios:
                disp = "Disponible" if s.disponible else "No disponible"
                lineas.append(f"  [{s.id_entidad}] {s.nombre} | ${s.precio_hora:,.0f}/h | {disp}")

            lineas += ["", "RESERVAS"]
            for r in reservas:
                lineas.append(
                    f"  [{r.id_reserva}] {r.cliente.nombre} → {r.servicio.nombre} | "
                    f"{r.horas}h | ${r.costo:,.0f} | {r.estado.value}"
                )

            lineas += ["", "=" * 58, "  Fin del reporte", "=" * 58]

            with open(ruta, "w", encoding="utf-8") as f:
                f.write("\n".join(lineas))

            toast(self.root, f"✓ Reporte exportado: {nombre}")
            log.info("Reporte", f"Archivo exportado: {ruta}")
        except Exception as ex:
            toast(self.root, f"Error al exportar: {ex}", error=True)

    def refrescar_publico(self):
        self._refrescar()


class App(tk.Tk):
    """Ventana principal de la aplicación. Contiene el sidebar de navegación
    y el área de contenido donde se muestran los paneles."""

    def __init__(self, gestor=None):
        super().__init__()
        self.title("Software FJ — Sistema de Gestión")
        self.geometry("1180x720")
        self.minsize(1000, 640)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.gestor    = gestor or GestorSistema()  # Usa un gestor existente o crea uno nuevo
        self._panels   = {}     # Diccionario de paneles por nombre de pestaña
        self._nav_btns = {}     # Diccionario de botones de navegación
        self._actual   = None   # Nombre del panel actualmente visible
        self._set_icono()
        self._construir_layout()
        self._mostrar("clientes")  # Pestaña inicial al abrir la app

    def _set_icono(self):
        """Genera y aplica un ícono PNG con las letras F y J directamente en código,
        sin depender de archivos externos."""
        try:
            import struct, zlib, tempfile

            def _png_fj(tam=32):
                az = (9, 105, 218, 255)   # Color azul (#0969da)
                bl = (255, 255, 255, 255) # Blanco

                pixels = [[az]*tam for _ in range(tam)]

                def rect(x0, y0, x1, y1):
                    # Pinta un rectángulo de píxeles blancos en la cuadrícula
                    for y in range(y0, y1):
                        for x in range(x0, x1):
                            if 0<=x<tam and 0<=y<tam:
                                pixels[y][x] = bl

                # Letra F
                rect(5, 5, 8, 27)   # trazo vertical
                rect(5, 5, 16, 8)   # barra superior
                rect(5, 14, 14, 17) # barra media

                # Letra J
                rect(18, 5, 27, 8)  # barra superior
                rect(23, 5, 26, 24) # trazo vertical
                rect(16, 21, 24, 24)# curva inferior

                # Construye el archivo PNG binario manualmente (sin librerías externas)
                def chunk(name, data):
                    c = name + data
                    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

                ihdr = struct.pack('>IIBBBBB', tam, tam, 8, 2, 0, 0, 0)
                raw  = b''
                for row in pixels:
                    raw += b'\x00'
                    for px in row:
                        raw += bytes(px[:3])

                return (b'\x89PNG\r\n\x1a\n'
                        + chunk(b'IHDR', ihdr)
                        + chunk(b'IDAT', zlib.compress(raw))
                        + chunk(b'IEND', b''))

            png_data = _png_fj(32)
            img = tk.PhotoImage(data=png_data)
            self._icono = img  # Guarda referencia para evitar que el GC lo elimine
            self.iconphoto(True, img)
        except Exception:
            pass  # Si falla, simplemente no se muestra ícono

    def _construir_layout(self):
        """Construye el sidebar izquierdo y el área de contenido derecha."""
        sidebar = tk.Frame(self, bg=PANEL, width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)  # Evita que el contenido redimensione el sidebar

        tk.Label(sidebar, text="Software FJ", font=("Segoe UI",14,"bold"),
                 bg=PANEL, fg=TEXT).pack(pady=(28,4), padx=20, anchor="w")
        tk.Label(sidebar, text="Sistema de gestión", font=F_SM,
                 bg=PANEL, fg=TEXT_DIM).pack(padx=20, anchor="w")
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=14, pady=18)

        # Crea un botón de navegación por cada pestaña
        for texto, key in [
            ("👤  Clientes",  "clientes"),
            ("🛠️   Servicios", "servicios"),
            ("📋  Reservas",  "reservas"),
            ("📊  Reporte",   "reporte"),
        ]:
            btn = self._nav_btn(sidebar, texto, key)
            btn.pack(fill="x", padx=10, pady=3)
            self._nav_btns[key] = btn

        # Espaciador flexible que empuja el reloj y el botón de tema hacia abajo
        tk.Frame(sidebar, bg=PANEL).pack(expand=True)

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=14)

        # Reloj y fecha actualizados cada segundo
        self._lbl_hora = tk.Label(sidebar, text="", font=("Consolas", 18, "bold"),
                                   bg=PANEL, fg=ACCENT)
        self._lbl_hora.pack(pady=(14, 2))
        self._lbl_fecha = tk.Label(sidebar, text="", font=("Segoe UI", 8),
                                    bg=PANEL, fg=TEXT_DIM)
        self._lbl_fecha.pack(pady=(0, 10))
        self._tick()

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=14)

        # Botón para alternar entre modo oscuro y claro
        icono = "☀  Modo claro" if _MODO_ACTUAL == "oscuro" else "🌙  Modo oscuro"
        btn_color = "#2d3748" if _MODO_ACTUAL == "oscuro" else "#d0d7de"
        btn_fg    = TEXT
        self._btn_tema = PillButton(sidebar, icono, self._toggle_tema,
                                    bg=btn_color, fg=btn_fg, w=190, h=36, font=F_SM)
        self._btn_tema.pack(fill="x")

        # Área donde se muestran los paneles
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Instancia todos los paneles (solo uno estará visible a la vez)
        self._panels["clientes"]  = PanelClientes(self.content, self.gestor, self)
        self._panels["servicios"] = PanelServicios(self.content, self.gestor, self)
        self._panels["reservas"]  = PanelReservas(self.content, self.gestor, self)
        self._panels["reporte"]   = PanelReporte(self.content, self.gestor, self)

    def _tick(self):
        """Actualiza la hora y fecha en el sidebar cada 1000ms."""
        ahora = datetime.now()
        self._lbl_hora.config(text=ahora.strftime("%H:%M:%S"))
        self._lbl_fecha.config(text=ahora.strftime("%d %b %Y"))
        self.after(1000, self._tick)

    def _nav_btn(self, parent, texto, key):
        """Crea un botón de navegación con indicador lateral de selección activa."""
        frm = tk.Frame(parent, bg=PANEL, cursor="hand2", height=38)
        frm.pack_propagate(False)
        inner = tk.Frame(frm, bg=PANEL, cursor="hand2")
        inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        lbl_ = tk.Label(inner, text=texto, font=F_BODY, bg=PANEL,
                        fg=TEXT_DIM, anchor="w", padx=14, cursor="hand2")
        lbl_.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Barra vertical de 3px que indica la pestaña activa
        indicator = tk.Frame(inner, bg=PANEL, width=3)
        indicator.place(relx=0, rely=0, relheight=1)

        def activar():
            # Resalta el botón y muestra la barra indicadora
            inner.config(bg=NAV_HOV); lbl_.config(bg=NAV_HOV, fg=TEXT)
            indicator.config(bg=ACCENT)

        def desactivar():
            # Restaura el aspecto inactivo
            inner.config(bg=PANEL); lbl_.config(bg=PANEL, fg=TEXT_DIM)
            indicator.config(bg=PANEL)

        frm._activar    = activar
        frm._desactivar = desactivar

        for w in (frm, inner, lbl_):
            w.bind("<Button-1>", lambda e, k=key: self._mostrar(k))
            w.bind("<Enter>", lambda e, i=inner, l=lbl_: (
                i.config(bg=NAV_HOV), l.config(bg=NAV_HOV)))
            w.bind("<Leave>", lambda e, k=key: None)

        return frm

    def _toggle_tema(self):
        """Cambia entre modo oscuro y claro reconstruyendo toda la UI."""
        nuevo = "claro" if _MODO_ACTUAL == "oscuro" else "oscuro"
        _cargar_tema(nuevo)
        gestor = self.gestor
        panel_actual = self._actual or "clientes"
        # Destruye todos los widgets y reconstruye con los nuevos colores
        for w in self.winfo_children(): w.destroy()
        self._panels = {}; self._nav_btns = {}; self._actual = None
        self.configure(bg=BG)
        self.gestor = gestor
        self._construir_layout()
        self._mostrar(panel_actual)

    def _mostrar(self, key: str):
        """Oculta el panel actual y muestra el panel correspondiente a key."""
        if self._actual and self._actual in self._nav_btns:
            self._nav_btns[self._actual]._desactivar()
        if self._actual:
            self._panels[self._actual].pack_forget()
        self._panels[key].pack(fill="both", expand=True)
        self._nav_btns[key]._activar()
        self._actual = key
        panel = self._panels[key]
        # Si el panel expone refrescar_publico, lo llama al entrar para mostrar datos actualizados
        if hasattr(panel, "refrescar_publico"):
            panel.refrescar_publico()

        self._fade_in()

    def _fade_in(self):
        """Simula un efecto fade-in con un Canvas superpuesto usando stipple decreciente."""
        ov = tk.Canvas(self.content, bg=BG, highlightthickness=0)
        ov.place(x=0, y=0, relwidth=1, relheight=1)
        pasos = ["gray75", "gray50", "gray25", "gray12"]  # De más opaco a más transparente

        def step(i):
            if i >= len(pasos):
                try: ov.destroy()
                except: pass
                return
            try:
                ov.update_idletasks()
                w = ov.winfo_width() or self.content.winfo_width()
                h = ov.winfo_height() or self.content.winfo_height()
                ov.delete("all")
                ov.create_rectangle(0, 0, w, h, fill=BG, stipple=pasos[i], outline="")
                self.content.after(38, lambda: step(i+1))
            except: pass

        self.content.after(10, lambda: step(0))


# SPLASH SCREEN

class SplashScreen(tk.Tk):
    """Pantalla de carga que se muestra antes de abrir la App.
    Muestra una barra de progreso animada y mensajes de estado."""

    _BG     = "#f6f8fa"
    _BORDER = "#d0d7de"
    _ACCENT = "#0969da"
    _ACCT2  = "#1a7f37"
    _DIM    = "#57606a"
    _VER    = "#6e7781"

    # Pasos de la barra de progreso: (porcentaje, mensaje)
    PASOS = [
        (10,  "Iniciando sistema..."),
        (30,  "Cargando módulos..."),
        (50,  "Preparando gestor..."),
        (70,  "Configurando interfaz..."),
        (90,  "Casi listo..."),
        (100, "¡Bienvenido!"),
    ]

    def __init__(self):
        super().__init__()
        self.overrideredirect(True)   # Quita la barra de título del sistema operativo
        self.configure(bg=self._BG)
        self.attributes("-topmost", True)
        ancho, alto = 380, 420
        # Centra la ventana en la pantalla
        x = (self.winfo_screenwidth()  - ancho) // 2
        y = (self.winfo_screenheight() - alto)  // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self._progreso = 0; self._paso_idx = 0; self._foto = None
        self._construir()
        self.after(200, self._animar_logo)
        self.after(400, self._ejecutar_paso)
        self.mainloop()

    def _cargar_imagen(self, ancho_px, alto_px):
        """Intenta cargar la imagen del splash desde rutas predefinidas.
        Primero intenta con Pillow; si no está instalada, usa tk.PhotoImage."""
        rutas = [
            r"C:\Users\Usuario\OneDrive\Documentos\Tarea numero 4 programacion\imagen splash.png",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagen splash.png"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagen_splash.png"),
        ]
        ruta = next((r for r in rutas if os.path.exists(r)), None)
        if not ruta:
            return None
        try:
            from PIL import Image, ImageTk
            img = Image.open(ruta).resize((ancho_px, alto_px), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except ImportError:
            pass  # Pillow no instalada, se intenta con tk.PhotoImage
        except Exception:
            return None
        try:
            raw    = tk.PhotoImage(file=ruta)
            factor = max(1, min(raw.width() // ancho_px, raw.height() // alto_px))
            return raw.subsample(factor, factor) if factor > 1 else raw
        except Exception:
            return None

    def _construir(self):
        """Construye todos los widgets de la pantalla splash."""
        borde = tk.Frame(self, bg=self._ACCENT, padx=2, pady=2)
        borde.pack(fill="both", expand=True)
        contenedor = tk.Frame(borde, bg=self._BG)
        contenedor.pack(fill="both", expand=True)

        zona_img = tk.Frame(contenedor, bg=self._BG)
        zona_img.pack(fill="x", pady=(22, 0))

        self._foto = self._cargar_imagen(100, 100)
        if self._foto:
            tk.Label(zona_img, image=self._foto, bg=self._BG, bd=0).pack()
        else:
            # Si no hay imagen, dibuja el logo animado en un Canvas
            self._logo_canvas = tk.Canvas(zona_img, width=90, height=90,
                                           bg=self._BG, highlightthickness=0)
            self._logo_canvas.pack()
            self._dibujar_logo(0)

        body = tk.Frame(contenedor, bg=self._BG, padx=36, pady=14)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Software FJ",
                 font=("Segoe UI", 22, "bold"),
                 bg=self._BG, fg=self._ACCENT).pack()
        tk.Label(body, text="Sistema Integral de Gestión",
                 font=("Segoe UI", 9),
                 bg=self._BG, fg=self._DIM).pack(pady=(2, 8))

        # Chips decorativos que indican tecnologías usadas
        chips = tk.Frame(body, bg=self._BG); chips.pack(pady=(0, 14))
        for txt, color in [("Python 3", self._ACCENT), ("OOP", self._ACCT2), ("Sin BD", "#9a6700")]:
            c = tk.Frame(chips, bg=color); c.pack(side="left", padx=4)
            tk.Label(c, text=f"  {txt}  ", font=("Segoe UI", 7, "bold"),
                     bg=color, fg="white").pack(ipady=2)

        tk.Frame(body, bg=self._BORDER, height=1).pack(fill="x", pady=(0, 10))

        # Etiqueta que muestra el mensaje del paso actual
        self._lbl_estado = tk.Label(body, text="Iniciando...",
                                    font=("Segoe UI", 8),
                                    bg=self._BG, fg=self._DIM, anchor="w")
        self._lbl_estado.pack(fill="x")

        # Barra de progreso: fondo gris + barra azul que crece
        self._barra_bg = tk.Frame(body, bg=self._BORDER, height=5)
        self._barra_bg.pack(fill="x", pady=(5, 0))
        self._barra_bg.pack_propagate(False)
        self._barra = tk.Frame(self._barra_bg, bg=self._ACCENT, height=5)
        self._barra.place(x=0, y=0, relheight=1, width=0)

        tk.Label(body, text="v1.0  —  Sin base de datos",
                 font=("Segoe UI", 7),
                 bg=self._BG, fg=self._VER).pack(side="bottom", anchor="e")

    def _dibujar_logo(self, progreso):
        """Dibuja el logo circular con las letras F y J en el Canvas,
        con un arco de progreso proporcional al valor recibido."""
        c = self._logo_canvas; c.delete("all")
        cx, cy, r = 27, 27, 24
        c.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#cce5ff", outline=self._BORDER)
        if progreso > 0:
            c.create_arc(cx-r, cy-r, cx+r, cy+r,
                         start=90, extent=-int(3.6*progreso),
                         fill=self._ACCENT, outline="", style="pieslice")
        ri = 17
        c.create_oval(cx-ri, cy-ri, cx+ri, cy+ri, fill=self._BG, outline=self._BG)
        c.create_text(cx-4, cy, text="F", font=("Segoe UI",9,"bold"),
                      fill=self._ACCENT, anchor="center")
        c.create_text(cx+5, cy, text="J", font=("Segoe UI",9,"bold"),
                      fill=self._ACCT2, anchor="center")

    def _animar_logo(self):
        """Llama a _dibujar_logo repetidamente para animar el arco del logo."""
        self._dibujar_logo(self._progreso)
        if self._progreso < 100:
            self.after(60, self._animar_logo)

    def _ejecutar_paso(self):
        """Avanza al siguiente paso de la barra, actualiza el mensaje y destruye
        la ventana cuando todos los pasos terminan."""
        if self._paso_idx >= len(self.PASOS):
            self.after(400, self.destroy); return
        objetivo, mensaje = self.PASOS[self._paso_idx]
        self._lbl_estado.config(text=mensaje)
        self._animar_barra(self._progreso, objetivo)
        self._progreso = objetivo; self._paso_idx += 1
        # Pasos iniciales más rápidos; los últimos con más pausa para sensación de carga
        self.after(260 if self._paso_idx <= 3 else 420, self._ejecutar_paso)

    def _animar_barra(self, desde, hasta, pasos=14):
        """Anima suavemente la barra de progreso interpolando entre desde y hasta."""
        def step(actual, n):
            if n <= 0:
                self._set_barra(hasta); return
            nuevo = actual + (hasta - actual) / max(n, 1)
            self._set_barra(nuevo)
            self.after(14, lambda: step(nuevo, n - 1))
        step(desde, pasos)

    def _set_barra(self, pct):
        """Ajusta el ancho de la barra azul al porcentaje indicado."""
        self.update_idletasks()
        total = self._barra_bg.winfo_width()
        self._barra.place(x=0, y=0, relheight=1, width=int(total * pct / 100))


if __name__ == "__main__":
    SplashScreen()   # Muestra la pantalla de carga; al cerrarse lanza la app principal
    App().mainloop()
