"""Aplicación de escritorio de Software FJ. Ejecutar este archivo con Python 3."""
import io
import logging
from contextlib import redirect_stdout
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from gestion import Gestion
from modelo import DatoInvalido, ErrorGestion
from principal import ejecutar

BASE = Path(__file__).resolve().parent


class Panel:
    """Mantiene las filas visibles de la sesión junto al gestor de dominio."""
    def __init__(self):
        self.gestion = Gestion()
        self.clientes, self.servicios, self.reservas = [], [], []
        self.pruebas = []
        # Datos iniciales ficticios para poder probar una reserva de inmediato.
        for codigo, nombre in [("C1", "Ana Ríos"), ("C2", "Luis Mora")]:
            self.operar("cliente", dict(codigo=codigo, nombre=nombre, correo=codigo+"@example.org"))
        for tipo, codigo, tarifa in [("sala", "S1", 30000), ("equipo", "E1", 10000), ("asesoria", "A1", 50000)]:
            self.operar("servicio", dict(tipo=tipo, codigo=codigo, tarifa=tarifa))

    def datos(self):
        return dict(clientes=self.clientes, servicios=self.servicios, reservas=self.reservas, pruebas=self.pruebas)

    def operar(self, accion, datos):
        g = self.gestion
        codigo = str(datos.get("codigo", "")).strip().upper()
        if accion == "cliente":
            nombre, correo = datos["nombre"].strip(), datos["correo"].strip()
            resultado = g.cliente(codigo, nombre, correo)
            self.clientes.append(dict(codigo=codigo, nombre=nombre, correo=correo))
        elif accion == "servicio":
            tipo, tarifa = datos["tipo"], datos["tarifa"]
            resultado = g.servicio(tipo, codigo, tarifa)
            self.servicios.append(dict(codigo=codigo, tipo=tipo, tarifa=float(tarifa)))
        elif accion == "reservar":
            cliente, recurso, horas = datos["cliente"], datos["servicio"], datos["horas"]
            resultado = g.reservar(codigo, cliente, recurso, horas)
            self.reservas.insert(0, dict(codigo=codigo, cliente=cliente, servicio=recurso, horas=int(float(horas)), estado="pendiente", total=None))
        elif accion in ("confirmar", "cancelar", "procesar"):
            reserva = next((r for r in self.reservas if r["codigo"] == codigo), None)
            if reserva is None:
                raise DatoInvalido("La reserva no existe.")
            if accion == "procesar":
                resultado = g.procesar(codigo, descuento=datos.get("descuento", 0), impuesto=datos.get("impuesto", 0))
                reserva["total"] = float(resultado.rsplit(" COP ", 1)[1])
                reserva["estado"] = "procesada"
            elif accion == "confirmar":
                resultado = g.confirmar(codigo)
                reserva["estado"] = "confirmada"
            else:
                resultado = g.cancelar(codigo)
                reserva["estado"] = "cancelada"
        elif accion == "simular":
            salida = io.StringIO()
            with redirect_stdout(salida):
                ejecutar()
            self.pruebas = []
            for linea in salida.getvalue().splitlines()[:-1]:
                caso, estado, detalle = linea.split(" | ", 2)
                self.pruebas.append(dict(caso=caso, estado=estado, detalle=detalle))
            resultado = salida.getvalue().splitlines()[-1]
        else:
            raise DatoInvalido("Operación desconocida.")
        logging.getLogger("panel_fj").info("%s | %s", accion, resultado)
        return resultado


NAV = "#182e3a"
HERO = "#16444a"
INK = "#203541"
TEAL = "#126b64"
PAPER = "#f4f7f6"
MUTED = "#52686e"
MINT = "#c9eadc"
WHITE = "#ffffff"
TITULOS = {"sala": "Sala de reuniones", "equipo": "Alquiler de equipos", "asesoria": "Asesoría especializada"}


def pesos(valor):
    return "$" + format(valor, ",.2f").replace(",", "_").replace(".", ",").replace("_", ".")


def etiqueta(parent, texto, size=11, color=INK, fondo=None, bold=False, serif=False):
    return tk.Label(parent, text=texto, fg=color, bg=fondo or parent.cget("bg"),
                    font=("Georgia" if serif else "Segoe UI", size, "bold" if bold else "normal"),
                    anchor="w", justify="left", bd=0)


def boton(parent, texto, cmd, fondo=TEAL, color=WHITE):
    return tk.Button(parent, text=texto, command=cmd, bg=fondo, fg=color, activebackground="#c7e7dc",
                     activeforeground=INK, font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                     cursor="hand2", padx=14, pady=7, highlightthickness=0)


def ilustrar(c):
    """Dibuja una sala isométrica con polígonos nativos de Tk."""
    def punto(x, y, z):
        return (157+(x-y)*.83, 130+(x+y)*.33-z*.78)

    def cara(coords, color):
        c.create_polygon([n for v in coords for n in punto(*v)], fill=color, outline=HERO, width=.65)

    def bloque(x,y,z,w,d,h,p):
        cara([(x+w,y,z),(x+w,y+d,z),(x+w,y+d,z+h),(x+w,y,z+h)],p[1])
        cara([(x,y+d,z),(x+w,y+d,z),(x+w,y+d,z+h),(x,y+d,z+h)],p[2])
        cara([(x,y,z+h),(x+w,y,z+h),(x+w,y+d,z+h),(x,y+d,z+h)],p[0])

    piedra=("#c1d4c7","#70928d","#8eaaa0")
    menta=("#c9eddb","#75aa9b","#97c2b0")
    madera=("#edb47e","#ad7956","#cb946a")
    oscuro=("#648987","#375d61","#486e70")
    bloque(-88,-72,0,176,144,6,piedra)
    bloque(-88,-72,6,5,144,85,menta)
    bloque(-83,-72,6,171,5,85,menta)
    for x in (-65,-20,25):
        bloque(x,-67,30,38,2,43,("#f6e9c9","#98a999","#dfd2b4"))
    def silla(x,y):
        bloque(x+4,y+4,7,9,9,13,oscuro)
        bloque(x,y,20,18,18,5,menta)
        bloque(x,y,25,18,3,13,menta)
    for x in (-41,-6,29):
        silla(x,-41)
    for x in (-43,38):
        bloque(x,-20,7,6,31,26,oscuro)
    bloque(-51,-23,33,105,42,5,madera)
    bloque(-6,-10,38,18,13,2,oscuro)
    bloque(-6,-10,40,18,2,11,oscuro)
    for x in (-41,-6,29):
        silla(x,23)
    bloque(56,-44,6,18,18,19,madera)
    x,y=punto(65,-35,25)
    for dx,dy in [(-12,-12),(12,-15),(-6,-23),(5,-21),(0,-28)]:
        c.create_polygon(x,y,x+dx-3,y+dy/2,x+dx,y+dy,x+dx+4,y+dy/2,fill="#44806d",outline="")


class Escritorio:
    def __init__(self, raiz):
        self.raiz = raiz
        self.panel = Panel()
        self.pagina = "Inicio"
        self.formulario = None
        raiz.title("Software FJ  ·  Centro de reservas")
        w=min(1180,raiz.winfo_screenwidth()-70)
        h=min(760,raiz.winfo_screenheight()-100)
        raiz.geometry(f"{w}x{h}+{max(0,(raiz.winfo_screenwidth()-w)//2)}+24")
        raiz.minsize(min(w,880),min(h,590))
        raiz.configure(bg=PAPER)
        estilo=ttk.Style(raiz)
        estilo.theme_use("clam")
        estilo.configure("Treeview",font=("Segoe UI",10),rowheight=35,background=WHITE,
                         fieldbackground=WHITE,foreground=INK,borderwidth=0)
        estilo.configure("Treeview.Heading",font=("Segoe UI",10,"bold"),background="#e2ece8",
                         foreground="#38554f",relief="flat",padding=(6,6))
        estilo.map("Treeview",background=[("selected","#cae6dd")],foreground=[("selected",INK)])
        estilo.configure("TCombobox",padding=5)
        barra=tk.Frame(raiz,bg=NAV,width=226)
        barra.pack(side="left",fill="y");barra.pack_propagate(False)
        marca=tk.Frame(barra,bg=NAV);marca.pack(fill="x",padx=16,pady=(27,40))
        etiqueta(marca," FJ ",19,HERO,MINT,True,True).pack(side="left")
        etiqueta(marca," Software FJ",13,WHITE,bold=True).pack(side="left")
        self.enlaces={}
        for pagina,signo in [("Inicio","⌂"),("Reservas","▤"),("Clientes","◉"),("Servicios","◇"),("Simulaciones","▷")]:
            btn=boton(barra,f" {signo}    {pagina}",lambda v=pagina:self.ver(v),NAV,"#d0e2e3")
            btn.configure(anchor="w");btn.pack(fill="x",padx=10,pady=2)
            self.enlaces[pagina]=btn
        etiqueta(barra,"Atanael Balaguera\nProgramación · Grupo 61",10,"#c1d6d5").pack(side="bottom",padx=15,pady=24,anchor="w")
        region=tk.Frame(raiz,bg=PAPER);region.pack(fill="both",expand=True)
        barra_sup=tk.Frame(region,bg=WHITE);barra_sup.pack(fill="x")
        self.ruta=etiqueta(barra_sup,"",10,MUTED);self.ruta.pack(side="left",padx=26,pady=13)
        etiqueta(barra_sup,"●  Sesión de escritorio",10,TEAL).pack(side="right",padx=25)
        self.cuerpo=tk.Frame(region,bg=PAPER);self.cuerpo.pack(fill="both",expand=True,padx=25,pady=(19,8))
        self.estado=tk.StringVar(value="Listo para registrar una reserva.")
        tk.Label(region,textvariable=self.estado,bg="#e0ece7",fg=HERO,anchor="w",padx=18,pady=6,
                 font=("Segoe UI",10)).pack(side="bottom",fill="x")
        self.ver("Inicio")

    def ver(self,pagina):
        self.pagina=pagina
        for w in self.cuerpo.winfo_children():
            w.destroy()
        self.ruta.config(text="Software FJ   /   "+pagina)
        for nombre,btn in self.enlaces.items():
            btn.configure(bg="#314c58" if nombre==pagina else NAV)
        if pagina=="Inicio":
            hero=tk.Frame(self.cuerpo,bg=HERO,height=184);hero.pack(fill="x");hero.pack_propagate(False)
            dibujo=tk.Canvas(hero,bg=HERO,width=302,height=184,highlightthickness=0)
            dibujo.pack(side="right",fill="y");ilustrar(dibujo)
            info=tk.Frame(hero,bg=HERO);info.pack(side="left",padx=24)
            etiqueta(info,"Centro de reservas",27,WHITE,serif=True).pack(anchor="w")
            etiqueta(info,"Salas, equipos y asesorías en un solo lugar.",11,"#d3e7e1").pack(anchor="w",pady=(3,12))
            boton(info,"＋ Nueva reserva",lambda:self.abrir("reservar"),MINT,HERO).pack(anchor="w")
            etiqueta(self.cuerpo,"Catálogo de servicios",17,serif=True).pack(anchor="w",pady=(13,5))
            cards=tk.Frame(self.cuerpo,bg=PAPER);cards.pack(fill="x")
            for i,(k,titulo) in enumerate(TITULOS.items()):
                cards.columnconfigure(i,weight=1,uniform="catalogo")
                f=tk.Frame(cards,bg=WHITE,highlightbackground="#d5dfdb",highlightthickness=1)
                f.grid(row=0,column=i,sticky="nsew",padx=(0,7 if i<2 else 0))
                line=tk.Frame(f,bg=["#78ad9e","#c49869","#9d94b1"][i],width=5);line.pack(side="left",fill="y")
                inner=tk.Frame(f,bg=WHITE);inner.pack(side="left",padx=8,pady=8)
                etiqueta(inner,titulo,10,bold=True).pack(anchor="w")
                servicios=[s for s in self.panel.servicios if s["tipo"]==k]
                libres=sum(not self.ocupado(s["codigo"]) for s in servicios)
                etiqueta(inner,f"{libres} de {len(servicios)} disponibles",9,MUTED).pack(anchor="w")
            self.titulo("Reservas recientes", "Ver todas",lambda:self.ver("Reservas"))
            self.lista_reservas(self.panel.reservas[:5])
        elif pagina=="Reservas":
            self.titulo("Reservas","＋ Nueva reserva",lambda:self.abrir("reservar"))
            self.lista_reservas(self.panel.reservas)
        elif pagina=="Clientes":
            self.titulo("Clientes","＋ Nuevo cliente",lambda:self.abrir("cliente"))
            self.tabla(["Código","Nombre","Correo"],[95,195,270],
                       [(c["codigo"],c["nombre"],c["correo"]) for c in self.panel.clientes])
        elif pagina=="Servicios":
            self.titulo("Servicios","＋ Nuevo servicio",lambda:self.abrir("servicio"))
            self.tabla(["Código","Servicio","Tarifa por hora","Disponibilidad"],[75,190,130,130],
                       [(s["codigo"],TITULOS[s["tipo"]],pesos(s["tarifa"]),"Ocupado" if self.ocupado(s["codigo"]) else "Disponible") for s in self.panel.servicios])
        else:
            self.titulo("Simulaciones","▷ Ejecutar 27 pruebas",self.simular)
            pruebas=self.panel.pruebas
            if pruebas:
                balance="     ·     ".join(f"{sum(r['estado']==k for r in pruebas)} {v}" for k,v in [("ACEPTADA","aceptadas"),("RECHAZADA","rechazadas"),("IMPREVISTA","imprevistas")])
                etiqueta(self.cuerpo,balance,13,TEAL,bold=True).pack(anchor="w",pady=(2,12))
            self.tabla(["Operación","Resultado","Detalle"],[205,110,340],
                       [(r["caso"],r["estado"],r["detalle"]) for r in pruebas],"Ejecuta las 27 pruebas para ver sus resultados.")

    def titulo(self,texto,accion,cmd):
        fila=tk.Frame(self.cuerpo,bg=PAPER);fila.pack(fill="x",pady=(9,8))
        etiqueta(fila,texto,18,serif=True).pack(side="left")
        boton(fila,accion,cmd,"#deebe5",HERO).pack(side="right")

    def ocupado(self,codigo):
        return any(r["servicio"]==codigo and r["estado"] in ("pendiente","confirmada") for r in self.panel.reservas)

    def tabla(self,cols,anchos,filas,vacio=""):
        area=tk.Frame(self.cuerpo,bg=WHITE);area.pack(fill="both",expand=True)
        tabla=ttk.Treeview(area,columns=cols,show="headings",selectmode="browse",height=3)
        scroll=ttk.Scrollbar(area,orient="vertical",command=tabla.yview)
        tabla.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right",fill="y");tabla.pack(fill="both",expand=True)
        for nombre,ancho in zip(cols,anchos):
            tabla.heading(nombre,text=nombre,anchor="w")
            tabla.column(nombre,width=ancho,minwidth=40,anchor="w")
        tabla.tag_configure("alterna",background="#f4f8f6")
        for i,fila in enumerate(filas):
            tabla.insert("","end",values=fila,tags=("alterna",) if i%2 else ())
        if not filas and vacio:
            etiqueta(area,vacio,10,MUTED).place(relx=.5,rely=.58,anchor="center")
        return tabla

    def lista_reservas(self,reservas):
        nombres={c["codigo"]:c["nombre"] for c in self.panel.clientes}
        controles=tk.Frame(self.cuerpo,bg=PAPER);controles.pack(side="bottom",fill="x",pady=(7,0))
        tabla=self.tabla(["Reserva","Cliente","Servicio","Horas","Estado","Total"],[78,153,83,55,109,100],
                         [(r["codigo"],nombres[r["cliente"]],r["servicio"],r["horas"],r["estado"].capitalize(),
                           pesos(r["total"]) if r["total"] is not None else "—") for r in reservas],
                         "Crea tu primera reserva con el botón Nueva reserva.")
        acciones={}
        def seleccionado(event=None):
            idx=tabla.selection()
            reserva=reservas[tabla.index(idx[0])] if idx else None
            for a,(btn,estados) in acciones.items():
                btn.config(state="normal" if reserva and reserva["estado"] in estados else "disabled")
            return reserva
        def operar(a):
            r=seleccionado()
            if r:self.abrir(a,r["codigo"])
        if reservas:
            etiqueta(controles,"Reserva seleccionada",10,MUTED).pack(side="left",padx=(0,8))
            for a,t,e in [("confirmar","Confirmar",("pendiente",)),("procesar","Cobrar",("confirmada",)),("cancelar","Cancelar",("pendiente","confirmada"))]:
                btn=boton(controles,t,lambda v=a:operar(v),"#e0eae5",HERO);btn.pack(side="left",padx=3)
                acciones[a]=(btn,e)
            tabla.selection_set(tabla.get_children()[0]);seleccionado()
            tabla.bind("<<TreeviewSelect>>",seleccionado)

    def simular(self):
        self.estado.set(self.panel.operar("simular",{}))
        self.ver("Simulaciones")

    def abrir(self,accion,codigo=""):
        titulos={"reservar":"Nueva reserva","servicio":"Nuevo servicio","cliente":"Nuevo cliente","confirmar":"Confirmar reserva","cancelar":"Cancelar reserva","procesar":"Cobrar reserva"}
        f=tk.Toplevel(self.raiz);self.formulario=f;f.withdraw();f.title(titulos[accion]);f.configure(bg=WHITE);f.transient(self.raiz)
        f.resizable(False,False)
        box=tk.Frame(f,bg=WHITE);box.pack(fill="both",padx=24,pady=20)
        etiqueta(box,titulos[accion],21,serif=True).pack(anchor="w",pady=(0,12))
        valores={};opciones={}
        def campo(clave,nombre,valor="",items=None):
            etiqueta(box,nombre,10,MUTED,bold=True).pack(anchor="w",pady=(6,3))
            var=tk.StringVar(f,value=valor);valores[clave]=var
            if items is None:
                e=ttk.Entry(box,textvariable=var,width=38,font=("Segoe UI",11));e.pack(fill="x",ipady=4)
            else:
                opciones[clave]={et:cod for cod,et in items}
                e=ttk.Combobox(box,textvariable=var,values=list(opciones[clave]),state="readonly",width=38,font=("Segoe UI",10))
                e.pack(fill="x")
                if items:e.current(0)
            return e
        def siguiente(pref,lista):
            codigos={obj["codigo"] for obj in lista};n=1
            while f"{pref}{n}" in codigos:n+=1
            return f"{pref}{n}"
        if accion=="cliente":
            campo("codigo","Código",siguiente("C",self.panel.clientes));campo("nombre","Nombre completo");campo("correo","Correo electrónico")
        elif accion=="servicio":
            campo("codigo","Código",siguiente("S",self.panel.servicios));campo("tipo","Tipo de servicio",items=TITULOS.items());campo("tarifa","Tarifa por hora (COP)")
        elif accion=="reservar":
            campo("codigo","Código",siguiente("R",self.panel.reservas))
            campo("cliente","Cliente",items=[(c["codigo"],c["nombre"]+" · "+c["codigo"]) for c in self.panel.clientes])
            campo("servicio","Servicio disponible",items=[(s["codigo"],TITULOS[s["tipo"]]+" · "+s["codigo"]) for s in self.panel.servicios if not self.ocupado(s["codigo"])])
            campo("horas","Duración en horas","1")
        else:
            etiqueta(box,"Reserva "+codigo,12,TEAL,bold=True).pack(anchor="w")
            if accion=="procesar":
                campo("descuento","Descuento (%)","0");campo("impuesto","Impuesto (%)","0")
        error=etiqueta(box,"",10,"#923c2b");error.config(wraplength=320);error.pack(fill="x",pady=5)
        def guardar():
            try:
                datos={k:opciones[k].get(v.get(),"") if k in opciones else v.get() for k,v in valores.items()}
                if codigo:datos["codigo"]=codigo
                if accion=="reservar" and not datos["servicio"]:
                    raise DatoInvalido("Registra un servicio disponible antes de reservar.")
                resultado=self.panel.operar(accion,datos)
            except (ErrorGestion,ValueError) as causa:
                logging.getLogger("panel_fj").exception("Operación rechazada: %s",accion)
                error.config(text=str(causa))
                return
            self.estado.set(resultado);f.destroy();self.ver(self.pagina)
        pie=tk.Frame(box,bg=WHITE);pie.pack(fill="x")
        boton(pie,"Volver",f.destroy,"#e5ece8",INK).pack(side="left")
        boton(pie,{"procesar":"Confirmar cobro","cancelar":"Cancelar reserva","confirmar":"Confirmar"}.get(accion,"Guardar"),guardar).pack(side="right")
        f.bind("<Escape>",lambda event:f.destroy());f.bind("<Return>",lambda event:guardar())
        f.update_idletasks();x=self.raiz.winfo_rootx()+(self.raiz.winfo_width()-f.winfo_reqwidth())//2
        y=self.raiz.winfo_rooty()+(self.raiz.winfo_height()-f.winfo_reqheight())//2
        f.geometry(f"+{max(0,x)}+{max(0,y)}");f.deiconify();f.grab_set();f.focus_set()
        return f


def iniciar():
    registro=logging.getLogger("panel_fj")
    registro.setLevel(logging.INFO)
    archivo=logging.FileHandler(BASE / "software_fj.log",encoding="utf-8")
    archivo.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    registro.addHandler(archivo)
    try:
        raiz=tk.Tk()
        Escritorio(raiz)
        raiz.mainloop()
    finally:
        registro.removeHandler(archivo)
        archivo.close()


if __name__ == "__main__":
    iniciar()

