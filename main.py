import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import tkinter as tk
from tkinter import ttk, messagebox

from sistema import GestorSistema
from servicios import ReservaSala, AlquilerEquipo, Asesoria
from reserva import EstadoReserva
from excepciones import SoftwareFJError
from logger import log


#  PALETA Y FUENTES  

BG       = "#0d1117"
PANEL    = "#161b22"
CARD     = "#1c2330"
BORDER   = "#30363d"
ACCENT   = "#58a6ff"
ACCENT2  = "#3fb950"
WARN     = "#f85149"
AMBER    = "#e3b341"
TEXT     = "#e6edf3"
TEXT_DIM = "#8b949e"

F_H1   = ("Segoe UI", 18, "bold")
F_H2   = ("Segoe UI", 13, "bold")
F_BODY = ("Segoe UI",  10)
F_SM   = ("Segoe UI",   9)
F_MONO = ("Consolas",  10)

ESTADO_COLOR = {
    "PENDIENTE":  AMBER,
    "CONFIRMADA": ACCENT2,
    "COMPLETADA": ACCENT,
    "CANCELADA":  WARN,
}


#  WIDGETS REUTILIZABLES


class PillButton(tk.Frame):
    def __init__(self, parent, text="", command=None,
                 bg=ACCENT, fg="white", w=130, h=32, font=F_BODY, **kw):
        super().__init__(parent, bg=BG, width=w, height=h, cursor="hand2")
        self.pack_propagate(False)
        self._bg = bg; self._cmd = command
        self._inner = tk.Frame(self, bg=bg, cursor="hand2")
        self._inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._lbl = tk.Label(self._inner, text=text, font=font, bg=bg, fg=fg, cursor="hand2")
        self._lbl.place(relx=.5, rely=.5, anchor="center")
        for w_ in (self, self._inner, self._lbl):
            w_.bind("<Enter>",    self._enter)
            w_.bind("<Leave>",    self._leave)
            w_.bind("<Button-1>", self._click)

    def _enter(self, _=None):
        c = self._lighten(self._bg)
        self._inner.config(bg=c); self._lbl.config(bg=c)

    def _leave(self, _=None):
        self._inner.config(bg=self._bg); self._lbl.config(bg=self._bg)

    def _click(self, _=None):
        if self._cmd: self._cmd()

    @staticmethod
    def _lighten(h):
        r = min(255, int(h[1:3],16)+25)
        g = min(255, int(h[3:5],16)+25)
        b = min(255, int(h[5:7],16)+25)
        return f"#{r:02x}{g:02x}{b:02x}"


class StyledEntry(tk.Frame):
    def __init__(self, parent, placeholder="", width=18, **kw):
        super().__init__(parent, bg=BG)
        self._ph = placeholder; self._active = False
        wrap = tk.Frame(self, bg=BORDER, padx=1, pady=1); wrap.pack(fill="x")
        inner = tk.Frame(wrap, bg=CARD); inner.pack(fill="x")
        self.var = tk.StringVar()
        self._e = tk.Entry(inner, textvariable=self.var, bg=CARD, fg=TEXT_DIM,
                           insertbackground=ACCENT, relief="flat",
                           font=F_BODY, bd=5, width=width, **kw)
        self._e.pack(fill="x")
        if placeholder:
            self._set_ph()
            self._e.bind("<FocusIn>",  self._clear)
            self._e.bind("<FocusOut>", self._restore)

    def _set_ph(self):
        self.var.set(self._ph); self._e.config(fg=TEXT_DIM); self._active=True

    def _clear(self, _=None):
        if self._active: self.var.set(""); self._e.config(fg=TEXT); self._active=False

    def _restore(self, _=None):
        if not self.var.get(): self._set_ph()

    def get(self):
        return "" if self._active else self.var.get().strip()

    def set(self, v):
        self.var.set(v); self._e.config(fg=TEXT); self._active=False

    def clear(self):
        self.var.set(""); self._set_ph()


class StyledCombo(tk.Frame):
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


def lbl(parent, text, font=F_SM, fg=TEXT_DIM, bg=CARD, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)


def separador(parent, bg=CARD):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(6,10))



#  TOAST

def toast(root, msg, error=False):
    color = WARN if error else ACCENT2
    t = tk.Toplevel(root)
    t.overrideredirect(True); t.attributes("-topmost", True)
    frm = tk.Frame(t, bg=color, padx=18, pady=10); frm.pack()
    tk.Label(frm, text=msg, font=F_BODY, bg=color, fg="white",
             wraplength=420).pack()
    t.update_idletasks()
    rx = root.winfo_x() + root.winfo_width()//2
    ry = root.winfo_y() + root.winfo_height() - 80
    t.geometry(f"+{rx - t.winfo_width()//2}+{ry}")
    t.after(3200, lambda: t.destroy() if t.winfo_exists() else None)



#  PANEL CLIENTES

class PanelClientes(tk.Frame):
    def __init__(self, parent, gestor: GestorSistema, root):
        super().__init__(parent, bg=BG)
        self.gestor = gestor; self.root = root
        self._construir()

    def _construir(self):
        # ── Título ──
        tk.Label(self, text="👤  Clientes", font=F_H1, bg=BG, fg=TEXT).pack(anchor="w", padx=30, pady=(24,4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(0,18))

        contenido = tk.Frame(self, bg=BG); contenido.pack(fill="both", expand=True, padx=30)
        contenido.columnconfigure(0, weight=1); contenido.columnconfigure(1, weight=2)

        # ── Formulario ──
        form_wrap = tk.Frame(contenido, bg=BORDER, padx=1, pady=1)
        form_wrap.grid(row=0, column=0, sticky="n", padx=(0,16))
        form = tk.Frame(form_wrap, bg=CARD, padx=20, pady=20); form.pack()

        lbl(form, "REGISTRAR CLIENTE", font=("Segoe UI",10,"bold"), fg=ACCENT).pack(anchor="w")
        separador(form)

        campos = [
            ("Identificación",  "CC-001"),
            ("Nombre completo", "Ana García"),
            ("Email",           "ana@email.com"),
            ("Teléfono",        "+57 300 000 0000"),
            ("Empresa",         "Opcional"),
        ]
        self.entries = {}
        for etiqueta, ph in campos:
            lbl(form, etiqueta).pack(anchor="w", pady=(6,2))
            e = StyledEntry(form, placeholder=ph, width=26)
            e.pack(fill="x")
            self.entries[etiqueta] = e

        fila_btn = tk.Frame(form, bg=CARD); fila_btn.pack(fill="x", pady=(16,0))
        PillButton(fila_btn, "✓  Registrar", self._registrar, bg=ACCENT2, w=150).pack(side="left", padx=(0,8))
        PillButton(fila_btn, "✕  Limpiar",   self._limpiar,   bg="#444c56", w=110).pack(side="left")

        # ── Lista ──
        lista_wrap = tk.Frame(contenido, bg=BORDER, padx=1, pady=1)
        lista_wrap.grid(row=0, column=1, sticky="nsew")
        lista_inner = tk.Frame(lista_wrap, bg=CARD); lista_inner.pack(fill="both", expand=True)

        lbl(lista_inner, "CLIENTES REGISTRADOS", font=("Segoe UI",10,"bold"),
            fg=ACCENT, bg=CARD).pack(anchor="w", padx=16, pady=(14,4))
        tk.Frame(lista_inner, bg=BORDER, height=1).pack(fill="x", padx=12)

        # Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("FJ.Treeview", background=CARD, foreground=TEXT,
                        fieldbackground=CARD, rowheight=28, font=F_BODY,
                        borderwidth=0)
        style.configure("FJ.Treeview.Heading", background=PANEL, foreground=TEXT_DIM,
                        font=("Segoe UI",9,"bold"), relief="flat")
        style.map("FJ.Treeview", background=[("selected","#2d3748")])

        cols = ("ID","Nombre","Email","Teléfono","Estado")
        self.tree = ttk.Treeview(lista_inner, columns=cols, show="headings",
                                 style="FJ.Treeview", height=14)
        for c, w in zip(cols, (90,160,180,130,80)):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")

        sb = ttk.Scrollbar(lista_inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(12,0), pady=8)
        sb.pack(side="right", fill="y", pady=8)

        # Botón desactivar
        btn_frame = tk.Frame(lista_inner, bg=CARD); btn_frame.pack(fill="x", padx=12, pady=(0,12))
        PillButton(btn_frame, "⊘  Desactivar seleccionado",
                   self._desactivar, bg=WARN, w=220, h=30).pack(side="left")

        self._refrescar()

    def _registrar(self):
        e = self.entries
        try:
            self.gestor.registrar_cliente(
                e["Identificación"].get(),
                e["Nombre completo"].get(),
                e["Email"].get(),
                e["Teléfono"].get(),
                e["Empresa"].get(),
            )
            toast(self.root, "✓ Cliente registrado exitosamente")
            self._limpiar(); self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _limpiar(self):
        for e in self.entries.values(): e.clear()

    def _desactivar(self):
        sel = self.tree.selection()
        if not sel: toast(self.root, "Selecciona un cliente primero", error=True); return
        ident = self.tree.item(sel[0])["values"][0]
        try:
            self.gestor.desactivar_cliente(str(ident))
            toast(self.root, f"Cliente '{ident}' desactivado")
            self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _refrescar(self):
        self.tree.delete(*self.tree.get_children())
        for c in self.gestor.listar_clientes():
            estado = "Activo" if c.activo else "Inactivo"
            self.tree.insert("", "end", values=(
                c.identificacion, c.nombre, c.email, c.telefono, estado
            ))



#  PANEL SERVICIOS

class PanelServicios(tk.Frame):
    def __init__(self, parent, gestor: GestorSistema, root):
        super().__init__(parent, bg=BG)
        self.gestor = gestor; self.root = root
        self._construir()

    def _construir(self):
        tk.Label(self, text="🛠️  Servicios", font=F_H1, bg=BG, fg=TEXT).pack(anchor="w", padx=30, pady=(24,4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(0,18))

        contenido = tk.Frame(self, bg=BG); contenido.pack(fill="both", expand=True, padx=30)
        contenido.columnconfigure(0, weight=1); contenido.columnconfigure(1, weight=2)

        # ── Formulario ──
        form_wrap = tk.Frame(contenido, bg=BORDER, padx=1, pady=1)
        form_wrap.grid(row=0, column=0, sticky="n", padx=(0,16))
        self.form = tk.Frame(form_wrap, bg=CARD, padx=20, pady=20); self.form.pack()

        lbl(self.form, "CREAR SERVICIO", font=("Segoe UI",10,"bold"), fg=ACCENT).pack(anchor="w")
        separador(self.form)

        lbl(self.form, "Tipo de servicio").pack(anchor="w", pady=(4,2))
        self.combo_tipo = StyledCombo(self.form,
            values=["Sala de reuniones","Alquiler de equipo","Asesoría especializada"], width=26)
        self.combo_tipo.pack(fill="x")
        self.combo_tipo.bind_select(self._cambiar_tipo)

        lbl(self.form, "ID del servicio").pack(anchor="w", pady=(10,2))
        self.e_id = StyledEntry(self.form, "SALA-01", width=26); self.e_id.pack(fill="x")

        lbl(self.form, "Nombre").pack(anchor="w", pady=(8,2))
        self.e_nombre = StyledEntry(self.form, "Sala Ejecutiva A", width=26); self.e_nombre.pack(fill="x")

        lbl(self.form, "Precio por hora ($)").pack(anchor="w", pady=(8,2))
        self.e_precio = StyledEntry(self.form, "80000", width=26); self.e_precio.pack(fill="x")

        # Contenedor de campos dinámicos
        self.frame_extra = tk.Frame(self.form, bg=CARD); self.frame_extra.pack(fill="x")
        self._campos_extra = {}
        self._mostrar_campos_sala()

        fila_btn = tk.Frame(self.form, bg=CARD); fila_btn.pack(fill="x", pady=(16,0))
        PillButton(fila_btn, "✓  Crear servicio", self._crear, bg=ACCENT2, w=160).pack(side="left", padx=(0,8))
        PillButton(fila_btn, "✕  Limpiar", self._limpiar, bg="#444c56", w=100).pack(side="left")

        # ── Lista ──
        lista_wrap = tk.Frame(contenido, bg=BORDER, padx=1, pady=1)
        lista_wrap.grid(row=0, column=1, sticky="nsew")
        lista_inner = tk.Frame(lista_wrap, bg=CARD); lista_inner.pack(fill="both", expand=True)

        lbl(lista_inner, "SERVICIOS REGISTRADOS", font=("Segoe UI",10,"bold"),
            fg=ACCENT, bg=CARD).pack(anchor="w", padx=16, pady=(14,4))
        tk.Frame(lista_inner, bg=BORDER, height=1).pack(fill="x", padx=12)

        cols = ("ID","Tipo","Nombre","Precio/h","Disponible")
        self.tree = ttk.Treeview(lista_inner, columns=cols, show="headings",
                                 style="FJ.Treeview", height=14)
        for c, w in zip(cols, (90,120,200,100,80)):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(lista_inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(12,0), pady=8)
        sb.pack(side="right", fill="y", pady=8)

        self._refrescar()

    def _limpiar_extra(self):
        for w in self.frame_extra.winfo_children(): w.destroy()
        self._campos_extra = {}

    def _mostrar_campos_sala(self):
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
        self._limpiar_extra()
        lbl(self.frame_extra, "Tipo / descripción del equipo").pack(anchor="w", pady=(8,2))
        e = StyledEntry(self.frame_extra, "Laptop 16GB RAM", width=26); e.pack(fill="x")
        self._campos_extra["tipo"] = e

        lbl(self.frame_extra, "Stock disponible (unidades)").pack(anchor="w", pady=(8,2))
        e2 = StyledEntry(self.frame_extra, "3", width=26); e2.pack(fill="x")
        self._campos_extra["stock"] = e2

    def _mostrar_campos_asesoria(self):
        self._limpiar_extra()
        lbl(self.frame_extra, "Especialidad").pack(anchor="w", pady=(8,2))
        e = StyledEntry(self.frame_extra, "Derecho Corporativo", width=26); e.pack(fill="x")
        self._campos_extra["especialidad"] = e

        lbl(self.frame_extra, "Nivel").pack(anchor="w", pady=(8,2))
        c = StyledCombo(self.frame_extra, values=["basico","intermedio","experto"], width=26)
        c.pack(fill="x"); c.set("basico")
        self._campos_extra["nivel"] = c

    def _cambiar_tipo(self, _=None):
        tipo = self.combo_tipo.get()
        if "Sala" in tipo:       self._mostrar_campos_sala()
        elif "equipo" in tipo:   self._mostrar_campos_equipo()
        elif "Asesor" in tipo:   self._mostrar_campos_asesoria()

    def _crear(self):
        tipo   = self.combo_tipo.get()
        id_s   = self.e_id.get()
        nombre = self.e_nombre.get()
        try:
            precio = float(self.e_precio.get())
        except ValueError:
            toast(self.root, "El precio debe ser un número", error=True); return
        try:
            if "Sala" in tipo:
                cap = int(self._campos_extra["capacidad"].get())
                svc = ReservaSala(id_s, nombre, precio, cap,
                                  self._proyector_var.get())
            elif "equipo" in tipo:
                tipo_eq = self._campos_extra["tipo"].get()
                stock   = int(self._campos_extra["stock"].get())
                svc = AlquilerEquipo(id_s, nombre, precio, tipo_eq, stock)
            elif "Asesor" in tipo:
                esp   = self._campos_extra["especialidad"].get()
                nivel = self._campos_extra["nivel"].get() or "basico"
                svc = Asesoria(id_s, nombre, precio, esp, nivel)
            else:
                toast(self.root, "Selecciona un tipo de servicio", error=True); return

            self.gestor.registrar_servicio(svc)
            toast(self.root, f"✓ Servicio '{nombre}' registrado")
            self._limpiar(); self._refrescar()
        except (SoftwareFJError, ValueError) as ex:
            toast(self.root, str(ex), error=True)

    def _limpiar(self):
        self.e_id.clear(); self.e_nombre.clear(); self.e_precio.clear()

    def _refrescar(self):
        self.tree.delete(*self.tree.get_children())
        for s in self.gestor.listar_servicios():
            tipo = type(s).__name__.replace("Reserva","").replace("Alquiler","Alq.")
            disp = "✓" if s.disponible else "✗"
            self.tree.insert("", "end", values=(
                s.id_entidad, tipo, s.nombre, f"${s.precio_hora:,.0f}", disp
            ))

    def refrescar_publico(self):
        self._refrescar()



#  PANEL RESERVAS

class PanelReservas(tk.Frame):
    def __init__(self, parent, gestor: GestorSistema, root):
        super().__init__(parent, bg=BG)
        self.gestor = gestor; self.root = root
        self._construir()

    def _construir(self):
        tk.Label(self, text="📋  Reservas", font=F_H1, bg=BG, fg=TEXT).pack(anchor="w", padx=30, pady=(24,4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(0,18))

        contenido = tk.Frame(self, bg=BG); contenido.pack(fill="both", expand=True, padx=30)
        contenido.columnconfigure(0, weight=1); contenido.columnconfigure(1, weight=2)

        # ── Formulario nueva reserva ──
        fw = tk.Frame(contenido, bg=BORDER, padx=1, pady=1)
        fw.grid(row=0, column=0, sticky="n", padx=(0,16))
        form = tk.Frame(fw, bg=CARD, padx=20, pady=20); form.pack()

        lbl(form, "NUEVA RESERVA", font=("Segoe UI",10,"bold"), fg=ACCENT).pack(anchor="w")
        separador(form)

        lbl(form, "ID Cliente").pack(anchor="w", pady=(4,2))
        self.e_cliente = StyledEntry(form, "CC-001", width=26); self.e_cliente.pack(fill="x")

        lbl(form, "ID Servicio").pack(anchor="w", pady=(8,2))
        self.e_servicio = StyledEntry(form, "SALA-A", width=26); self.e_servicio.pack(fill="x")

        lbl(form, "Duración (horas)").pack(anchor="w", pady=(8,2))
        self.e_horas = StyledEntry(form, "2.0", width=26); self.e_horas.pack(fill="x")

        lbl(form, "Descuento (%)").pack(anchor="w", pady=(8,2))
        self.e_desc = StyledEntry(form, "0", width=26); self.e_desc.pack(fill="x")

        lbl(form, "Notas").pack(anchor="w", pady=(8,2))
        self.e_notas = StyledEntry(form, "Opcional", width=26); self.e_notas.pack(fill="x")

        # IVA
        self.iva_var = tk.BooleanVar(value=True)
        fila_iva = tk.Frame(form, bg=CARD); fila_iva.pack(anchor="w", pady=(10,0))
        tk.Checkbutton(fila_iva, text="Aplicar IVA (19%)", variable=self.iva_var,
                       bg=CARD, fg=TEXT, selectcolor=CARD,
                       activebackground=CARD, font=F_BODY).pack(side="left")

        # Parámetros extra
        lbl(form, "Parámetros extra (opcional)").pack(anchor="w", pady=(12,4))
        lbl(form, "Personas / Unidades / Nivel", fg="#6a7280").pack(anchor="w", pady=(0,2))
        self.e_extra1 = StyledEntry(form, "ej: 5  ó  basico", width=26); self.e_extra1.pack(fill="x")

        self._check_vars = {
            "usar_proyector":  tk.BooleanVar(),
            "seguro":          tk.BooleanVar(),
            "incluir_informe": tk.BooleanVar(),
        }
        checks = [("🖥 Usar proyector","usar_proyector"),
                  ("🔒 Seguro de equipo (+5%)","seguro"),
                  ("📄 Incluir informe (+$50K)","incluir_informe")]
        for txt, key in checks:
            tk.Checkbutton(form, text=txt, variable=self._check_vars[key],
                           bg=CARD, fg=TEXT, selectcolor=CARD,
                           activebackground=CARD, font=F_SM).pack(anchor="w")

        fila_btn = tk.Frame(form, bg=CARD); fila_btn.pack(fill="x", pady=(14,0))
        PillButton(fila_btn, "✓  Crear reserva", self._crear, bg=ACCENT2, w=160).pack(side="left", padx=(0,8))
        PillButton(fila_btn, "✕  Limpiar", self._limpiar, bg="#444c56", w=100).pack(side="left")

        # ── Lista de reservas ──
        lw = tk.Frame(contenido, bg=BORDER, padx=1, pady=1)
        lw.grid(row=0, column=1, sticky="nsew")
        li = tk.Frame(lw, bg=CARD); li.pack(fill="both", expand=True)

        lbl(li, "RESERVAS", font=("Segoe UI",10,"bold"), fg=ACCENT, bg=CARD).pack(anchor="w", padx=16, pady=(14,4))
        tk.Frame(li, bg=BORDER, height=1).pack(fill="x", padx=12)

        cols = ("ID","Cliente","Servicio","Horas","Costo","Estado")
        self.tree = ttk.Treeview(li, columns=cols, show="headings",
                                 style="FJ.Treeview", height=10)
        anchos = (110,120,160,55,100,90)
        for c, w in zip(cols, anchos):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(li, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(12,0), pady=8)
        sb.pack(side="right", fill="y", pady=8)

        # Acciones sobre reserva seleccionada
        acc = tk.Frame(li, bg=CARD); acc.pack(fill="x", padx=12, pady=(0,12))
        for txt, cmd, color in [
            ("✓ Confirmar", self._confirmar, ACCENT2),
            ("✔ Completar", self._completar, ACCENT),
            ("✕ Cancelar",  self._cancelar,  WARN),
        ]:
            PillButton(acc, txt, cmd, bg=color, w=110, h=28, font=F_SM).pack(side="left", padx=(0,6))

        self._refrescar()

    def _crear(self):
        try:
            horas   = float(self.e_horas.get())
            desc_pct = float(self.e_desc.get() or "0")
            kwargs = {}

            extra1 = self.e_extra1.get()
            if extra1:
                try:   kwargs["num_personas"] = int(extra1); kwargs["cantidad_unidades"] = int(extra1)
                except ValueError: kwargs["nivel_override"] = extra1

            for key, var in self._check_vars.items():
                if var.get(): kwargs[key] = True

            r = self.gestor.crear_reserva(
                self.e_cliente.get(), self.e_servicio.get(), horas,
                con_iva=self.iva_var.get(),
                descuento=desc_pct/100,
                notas=self.e_notas.get(),
                **kwargs,
            )
            toast(self.root, f"✓ Reserva {r.id_reserva} creada — ${r.costo:,.0f}")
            self._limpiar(); self._refrescar()
        except (SoftwareFJError, ValueError) as ex:
            toast(self.root, str(ex), error=True)

    def _limpiar(self):
        for e in (self.e_cliente, self.e_servicio, self.e_horas,
                  self.e_desc, self.e_notas, self.e_extra1): e.clear()
        for v in self._check_vars.values(): v.set(False)

    def _id_seleccionado(self):
        sel = self.tree.selection()
        if not sel: toast(self.root, "Selecciona una reserva primero", error=True); return None
        return self.tree.item(sel[0])["values"][0]

    def _confirmar(self):
        id_r = self._id_seleccionado()
        if not id_r: return
        try:
            self.gestor.confirmar_reserva(str(id_r))
            toast(self.root, f"Reserva {id_r} confirmada ✓")
            self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _completar(self):
        id_r = self._id_seleccionado()
        if not id_r: return
        try:
            self.gestor.completar_reserva(str(id_r))
            toast(self.root, f"Reserva {id_r} completada ✓")
            self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _cancelar(self):
        id_r = self._id_seleccionado()
        if not id_r: return
        try:
            self.gestor.cancelar_reserva(str(id_r), "Cancelada desde interfaz")
            toast(self.root, f"Reserva {id_r} cancelada")
            self._refrescar()
        except SoftwareFJError as ex:
            toast(self.root, str(ex), error=True)

    def _refrescar(self):
        self.tree.delete(*self.tree.get_children())
        for r in self.gestor.listar_reservas():
            self.tree.insert("", "end", values=(
                r.id_reserva, r.cliente.nombre[:14],
                r.servicio.nombre[:18],
                r.horas, f"${r.costo:,.0f}", r.estado.value
            ))

    def refrescar_publico(self):
        self._refrescar()



#  PANEL REPORTE
═════
class PanelReporte(tk.Frame):
    def __init__(self, parent, gestor: GestorSistema, root):
        super().__init__(parent, bg=BG)
        self.gestor = gestor; self.root = root
        self._construir()

    def _construir(self):
        tk.Label(self, text="📊  Reporte General", font=F_H1, bg=BG, fg=TEXT).pack(anchor="w", padx=30, pady=(24,4))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(0,20))

        self.contenedor = tk.Frame(self, bg=BG)
        self.contenedor.pack(fill="both", expand=True, padx=30)
        self._refrescar()

    def _refrescar(self):
        for w in self.contenedor.winfo_children(): w.destroy()

        clientes  = self.gestor.listar_clientes()
        servicios = self.gestor.listar_servicios()
        reservas  = self.gestor.listar_reservas()

        confirmadas = sum(1 for r in reservas if r.estado == EstadoReserva.CONFIRMADA)
        completadas = sum(1 for r in reservas if r.estado == EstadoReserva.COMPLETADA)
        canceladas  = sum(1 for r in reservas if r.estado == EstadoReserva.CANCELADA)
        pendientes  = sum(1 for r in reservas if r.estado == EstadoReserva.PENDIENTE)
        ingresos    = sum(r.costo for r in reservas
                         if r.estado in (EstadoReserva.CONFIRMADA, EstadoReserva.COMPLETADA))

        # Tarjetas KPI
        kpis = tk.Frame(self.contenedor, bg=BG); kpis.pack(fill="x", pady=(0,20))

        datos_kpi = [
            ("👤 Clientes",     str(len(clientes)),     ACCENT),
            ("🛠️ Servicios",    str(len(servicios)),    ACCENT2),
            ("📋 Reservas",     str(len(reservas)),     AMBER),
            ("💰 Ingresos",     f"${ingresos:,.0f}",   "#c9d1d9"),
        ]
        for titulo, valor, color in datos_kpi:
            card = tk.Frame(kpis, bg=BORDER, padx=1, pady=1)
            card.pack(side="left", expand=True, fill="x", padx=6)
            inner = tk.Frame(card, bg=CARD, padx=20, pady=16); inner.pack(fill="both")
            tk.Label(inner, text=titulo, font=F_SM, bg=CARD, fg=TEXT_DIM).pack(anchor="w")
            tk.Label(inner, text=valor, font=("Segoe UI",22,"bold"), bg=CARD, fg=color).pack(anchor="w")

        # Detalle reservas
        det_wrap = tk.Frame(self.contenedor, bg=BORDER, padx=1, pady=1)
        det_wrap.pack(fill="x", pady=(0,16))
        det = tk.Frame(det_wrap, bg=CARD, padx=24, pady=18); det.pack(fill="both")

        lbl(det, "DESGLOSE DE RESERVAS", font=("Segoe UI",10,"bold"), fg=ACCENT).pack(anchor="w")
        tk.Frame(det, bg=BORDER, height=1).pack(fill="x", pady=(8,12))

        fila_estados = tk.Frame(det, bg=CARD); fila_estados.pack(fill="x")
        for estado, cant, color in [
            ("Pendientes",  pendientes,  AMBER),
            ("Confirmadas", confirmadas, ACCENT2),
            ("Completadas", completadas, ACCENT),
            ("Canceladas",  canceladas,  WARN),
        ]:
            bloque = tk.Frame(fila_estados, bg=CARD); bloque.pack(side="left", expand=True)
            tk.Label(bloque, text=str(cant), font=("Segoe UI",20,"bold"),
                     bg=CARD, fg=color).pack()
            tk.Label(bloque, text=estado, font=F_SM, bg=CARD, fg=TEXT_DIM).pack()

        # Botón refrescar
        tk.Frame(self.contenedor, bg=BG, height=10).pack()
        PillButton(self.contenedor, "↻  Actualizar reporte", self._refrescar,
                   bg="#444c56", w=180).pack()

    def refrescar_publico(self):
        self._refrescar()



#  VENTANA PRINCIPAL

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Software FJ — Sistema de Gestión")
        self.geometry("1180x720")
        self.minsize(1000, 640)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.gestor = GestorSistema()
        self._panels = {}
        self._nav_btns = {}
        self._actual = None

        self._construir_layout()
        self._mostrar("clientes")

    def _construir_layout(self):
        # ── Sidebar ──
        sidebar = tk.Frame(self, bg=PANEL, width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo
        tk.Label(sidebar, text="Software FJ", font=("Segoe UI",14,"bold"),
                 bg=PANEL, fg=TEXT).pack(pady=(28,4), padx=20, anchor="w")
        tk.Label(sidebar, text="Sistema de gestión", font=F_SM,
                 bg=PANEL, fg=TEXT_DIM).pack(padx=20, anchor="w")
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=14, pady=18)

        # Botones de navegación
        nav_items = [
            ("👤  Clientes",   "clientes"),
            ("🛠️   Servicios",  "servicios"),
            ("📋  Reservas",   "reservas"),
            ("📊  Reporte",    "reporte"),
        ]
        for texto, key in nav_items:
            btn = self._nav_btn(sidebar, texto, key)
            btn.pack(fill="x", padx=10, pady=3)
            self._nav_btns[key] = btn

        # Separador inferior
        tk.Frame(sidebar, bg=BG).pack(expand=True)
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=14)
        tk.Label(sidebar, text="v1.0 — Sin BD", font=F_SM,
                 bg=PANEL, fg=TEXT_DIM).pack(pady=14)

        # ── Área de contenido ──
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Crear paneles
        self._panels["clientes"]  = PanelClientes(self.content, self.gestor, self)
        self._panels["servicios"] = PanelServicios(self.content, self.gestor, self)
        self._panels["reservas"]  = PanelReservas(self.content, self.gestor, self)
        self._panels["reporte"]   = PanelReporte(self.content, self.gestor, self)

    def _nav_btn(self, parent, texto, key):
        """Botón de barra lateral con estado activo/inactivo."""
        frm = tk.Frame(parent, bg=PANEL, cursor="hand2", height=38)
        frm.pack_propagate(False)

        inner = tk.Frame(frm, bg=PANEL, cursor="hand2")
        inner.place(relx=0, rely=0, relwidth=1, relheight=1)

        lbl_ = tk.Label(inner, text=texto, font=F_BODY, bg=PANEL,
                        fg=TEXT_DIM, anchor="w", padx=14, cursor="hand2")
        lbl_.place(relx=0, rely=0, relwidth=1, relheight=1)

        indicator = tk.Frame(inner, bg=PANEL, width=3)
        indicator.place(relx=0, rely=0, relheight=1)

        def activar():
            inner.config(bg="#1f2937"); lbl_.config(bg="#1f2937", fg=TEXT)
            indicator.config(bg=ACCENT)

        def desactivar():
            inner.config(bg=PANEL); lbl_.config(bg=PANEL, fg=TEXT_DIM)
            indicator.config(bg=PANEL)

        frm._activar   = activar
        frm._desactivar = desactivar

        for w in (frm, inner, lbl_):
            w.bind("<Button-1>", lambda e, k=key: self._mostrar(k))
            w.bind("<Enter>", lambda e, i=inner, l=lbl_: (
                i.config(bg="#1f2937"), l.config(bg="#1f2937")))
            w.bind("<Leave>", lambda e, k=key: None)

        return frm

    def _mostrar(self, key: str):
        # Desactivar botón anterior
        if self._actual and self._actual in self._nav_btns:
            self._nav_btns[self._actual]._desactivar()

        # Ocultar panel anterior
        if self._actual:
            self._panels[self._actual].pack_forget()

        # Mostrar nuevo panel
        self._panels[key].pack(fill="both", expand=True)
        self._nav_btns[key]._activar()
        self._actual = key

        # Refrescar si el panel lo soporta
        panel = self._panels[key]
        if hasattr(panel, "refrescar_publico"):
            panel.refrescar_publico()



#  PUNTO DE ENTRADA

if __name__ == "__main__":
    app = App()
    app.mainloop()
