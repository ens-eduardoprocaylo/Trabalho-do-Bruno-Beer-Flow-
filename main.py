
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

DB_NAME = "beerflow.db"
LIMITE_CRITICO_LITROS = 5.0
LIMITE_LIMPEZA_LITROS = 1.5


def conectar():
    return sqlite3.connect(DB_NAME)


def criar_banco():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cervejas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS barris (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cerveja_id INTEGER NOT NULL,
            volume_total REAL NOT NULL,
            volume_atual REAL NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (cerveja_id) REFERENCES cervejas(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barril_id INTEGER NOT NULL,
            quantidade_litros REAL NOT NULL,
            data_hora TEXT NOT NULL,
            FOREIGN KEY (barril_id) REFERENCES barris(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barril_id INTEGER NOT NULL,
            mensagem TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            FOREIGN KEY (barril_id) REFERENCES barris(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        salt = secrets.token_hex(16)
        senha_hash = hashlib.pbkdf2_hmac(
            "sha256", "BeerFlow@2026".encode("utf-8"), bytes.fromhex(salt), 120000
        ).hex()
        cur.execute(
            "INSERT INTO usuarios (usuario, nome, senha_hash, salt) VALUES (?, ?, ?, ?)",
            ("admin", "Administrador", senha_hash, salt)
        )

    conn.commit()
    conn.close()


class BeerFlowApp:
    def __init__(self, root):
        self.root = root
        self.usuario_atual = None
        self.root.title("BeerFlow • Acesso")
        self.root.geometry("980x620")
        self.root.minsize(900, 580)
        self.root.configure(bg="#F4F1EC")

        self.configurar_estilos()
        self.criar_tela_login()

    def validar_decimal(self, valor):
        """Permite somente números e um separador decimal (vírgula ou ponto)."""
        if valor == "":
            return True
        if any(c not in "0123456789,." for c in valor):
            return False
        return valor.count(",") + valor.count(".") <= 1

    def validar_inteiro(self, valor):
        """Permite somente números inteiros positivos durante a digitação."""
        return valor == "" or valor.isdigit()

    def configurar_estilos(self):
        # Paleta inspirada em cervejarias artesanais: carvão, creme e âmbar.
        self.cores = {
            "fundo": "#F4F1EC",
            "sidebar": "#211C18",
            "sidebar_2": "#2C2520",
            "superficie": "#FFFFFF",
            "superficie_2": "#FAF8F5",
            "texto": "#241F1B",
            "muted": "#786F68",
            "muted_2": "#AAA19A",
            "borda": "#E8E1DA",
            "borda_forte": "#D8CEC4",
            "ambar": "#D88924",
            "ambar_escuro": "#A86212",
            "ambar_claro": "#FFF2DF",
            "verde": "#2E7A55",
            "verde_claro": "#EAF6EF",
            "azul": "#426B91",
            "azul_claro": "#EAF1F7",
            "vermelho": "#B6534E",
            "vermelho_claro": "#FBEDEC",
            "cinza_claro": "#F0ECE7",
        }

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background=self.cores["fundo"])
        style.configure("Surface.TFrame", background=self.cores["superficie"])
        style.configure("Card.TFrame", background=self.cores["superficie"])
        style.configure("Muted.TLabel", background=self.cores["fundo"], foreground=self.cores["muted"], font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=self.cores["superficie"], foreground=self.cores["texto"], font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=self.cores["superficie"], foreground=self.cores["texto"], font=("Segoe UI Semibold", 12))
        style.configure("Section.TLabel", background=self.cores["fundo"], foreground=self.cores["texto"], font=("Segoe UI Semibold", 18))
        style.configure("Hint.TLabel", background=self.cores["superficie"], foreground=self.cores["muted"], font=("Segoe UI", 9))

        style.configure(
            "TEntry",
            fieldbackground="#FFFFFF",
            foreground=self.cores["texto"],
            padding=10,
            bordercolor=self.cores["borda_forte"],
            lightcolor=self.cores["borda_forte"],
            darkcolor=self.cores["borda_forte"],
            relief="flat"
        )
        style.map("TEntry", bordercolor=[("focus", self.cores["ambar"])])

        style.configure(
            "TCombobox",
            fieldbackground="#FFFFFF",
            background="#FFFFFF",
            foreground=self.cores["texto"],
            padding=9,
            bordercolor=self.cores["borda_forte"],
            lightcolor=self.cores["borda_forte"],
            darkcolor=self.cores["borda_forte"],
            arrowcolor=self.cores["ambar_escuro"]
        )
        style.map("TCombobox", bordercolor=[("focus", self.cores["ambar"])])

        style.configure(
            "TSpinbox",
            fieldbackground="#FFFFFF",
            background="#FFFFFF",
            foreground=self.cores["texto"],
            padding=9,
            bordercolor=self.cores["borda_forte"],
            lightcolor=self.cores["borda_forte"],
            darkcolor=self.cores["borda_forte"],
            arrowcolor=self.cores["ambar_escuro"]
        )

        style.configure(
            "Primary.TButton",
            background=self.cores["ambar"],
            foreground="#FFFFFF",
            padding=(18, 11),
            font=("Segoe UI Semibold", 10),
            borderwidth=0,
            focusthickness=0,
            relief="flat"
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.cores["ambar_escuro"]), ("pressed", self.cores["ambar_escuro"]), ("disabled", "#DCC6A9")]
        )
        style.configure(
            "Secondary.TButton",
            background=self.cores["cinza_claro"],
            foreground=self.cores["texto"],
            padding=(16, 10),
            font=("Segoe UI Semibold", 10),
            borderwidth=0,
            relief="flat"
        )
        style.map("Secondary.TButton", background=[("active", "#E2DCD5")])
        style.configure(
            "Danger.TButton",
            background=self.cores["vermelho_claro"],
            foreground=self.cores["vermelho"],
            padding=(16, 10),
            font=("Segoe UI Semibold", 10),
            borderwidth=0,
            relief="flat"
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#F4D8D6"), ("disabled", "#F1EEEB")],
            foreground=[("disabled", "#AAA39B")]
        )

        style.configure(
            "Treeview",
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground=self.cores["texto"],
            rowheight=40,
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#F5F1EC",
            foreground="#615850",
            font=("Segoe UI Semibold", 9),
            relief="flat",
            padding=(10, 11)
        )
        style.map("Treeview.Heading", background=[("active", "#ECE5DD")])
        style.map(
            "Treeview",
            background=[("selected", self.cores["ambar_claro"])],
            foreground=[("selected", self.cores["texto"])]
        )

        style.configure("Reports.TNotebook", background=self.cores["fundo"], borderwidth=0)
        style.configure(
            "Reports.TNotebook.Tab",
            background=self.cores["cinza_claro"],
            foreground=self.cores["muted"],
            padding=(18, 10),
            font=("Segoe UI Semibold", 9),
            borderwidth=0
        )
        style.map(
            "Reports.TNotebook.Tab",
            background=[("selected", self.cores["superficie"]), ("active", "#E8E1D9")],
            foreground=[("selected", self.cores["texto"])]
        )

    def criar_tela_login(self):
        for w in self.root.winfo_children():
            w.destroy()

        self.root.title("BeerFlow • Login")
        self.root.geometry("980x620")
        self.root.minsize(900, 580)
        self.root.configure(bg=self.cores["fundo"])

        shell = tk.Frame(self.root, bg=self.cores["fundo"])
        shell.pack(fill="both", expand=True)

        hero = tk.Frame(shell, bg=self.cores["sidebar"], width=430)
        hero.pack(side="left", fill="y")
        hero.pack_propagate(False)

        logo = tk.Frame(hero, bg=self.cores["ambar"], width=62, height=62)
        logo.pack(anchor="w", padx=46, pady=(56, 30))
        logo.pack_propagate(False)
        tk.Label(logo, text="BF", bg=self.cores["ambar"], fg="#FFFFFF", font=("Segoe UI Semibold", 20)).pack(expand=True)

        tk.Label(hero, text="BeerFlow", bg=self.cores["sidebar"], fg="#FFFFFF", font=("Segoe UI Semibold", 31)).pack(anchor="w", padx=46)
        tk.Label(hero, text="GESTÃO INTELIGENTE DE BARRIS", bg=self.cores["sidebar"], fg=self.cores["ambar"], font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=48, pady=(7, 24))
        tk.Label(
            hero,
            text="Controle estoque, registre vendas e acompanhe o desempenho do evento em um só lugar.",
            bg=self.cores["sidebar"], fg="#D1C8C0", font=("Segoe UI", 12),
            justify="left", wraplength=320
        ).pack(anchor="w", padx=46)

        recursos = tk.Frame(hero, bg=self.cores["sidebar"])
        recursos.pack(anchor="w", padx=46, pady=(42, 0))
        for texto in ("Estoque em tempo real", "Vendas e limpeza controladas", "Relatórios com filtros e gráficos"):
            linha = tk.Frame(recursos, bg=self.cores["sidebar"])
            linha.pack(fill="x", pady=6)
            tk.Label(linha, text="✓", bg=self.cores["sidebar"], fg="#72C99A", font=("Segoe UI Semibold", 11)).pack(side="left", padx=(0, 9))
            tk.Label(linha, text=texto, bg=self.cores["sidebar"], fg="#E7E0DA", font=("Segoe UI", 10)).pack(side="left")

        login_area = tk.Frame(shell, bg=self.cores["fundo"])
        login_area.pack(side="left", fill="both", expand=True)

        card = tk.Frame(login_area, bg=self.cores["superficie"], highlightthickness=1, highlightbackground=self.cores["borda"])
        card.place(relx=.5, rely=.5, anchor="center", width=390, height=430)

        tk.Label(card, text="Bem-vindo", bg=self.cores["superficie"], fg=self.cores["texto"], font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=34, pady=(34, 4))
        tk.Label(card, text="Entre com seu usuário para acessar o BeerFlow.", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=34, pady=(0, 26))

        tk.Label(card, text="USUÁRIO", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=34, pady=(0, 6))
        self.login_usuario = ttk.Entry(card)
        self.login_usuario.pack(fill="x", padx=34)

        tk.Label(card, text="SENHA", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=34, pady=(18, 6))
        self.login_senha = ttk.Entry(card, show="•")
        self.login_senha.pack(fill="x", padx=34)

        self.mostrar_senha_var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(
            card, text="Mostrar senha", variable=self.mostrar_senha_var, command=self.alternar_visibilidade_senha,
            bg=self.cores["superficie"], activebackground=self.cores["superficie"], fg=self.cores["muted"],
            activeforeground=self.cores["texto"], selectcolor=self.cores["superficie"], font=("Segoe UI", 8), bd=0
        )
        chk.pack(anchor="w", padx=30, pady=(8, 12))

        ttk.Button(card, text="Entrar no BeerFlow", style="Primary.TButton", command=self.autenticar_login).pack(fill="x", padx=34)
        self.lbl_login_erro = tk.Label(card, text="", bg=self.cores["superficie"], fg=self.cores["vermelho"], font=("Segoe UI", 9))
        self.lbl_login_erro.pack(anchor="w", padx=34, pady=(12, 0))

        info = tk.Frame(card, bg=self.cores["superficie_2"])
        info.pack(fill="x", padx=34, pady=(17, 0))
        tk.Label(info, text="PRIMEIRO ACESSO", bg=self.cores["superficie_2"], fg=self.cores["ambar_escuro"], font=("Segoe UI Semibold", 7)).pack(anchor="w", padx=12, pady=(9, 2))
        tk.Label(info, text="Usuário: admin   •   Senha: BeerFlow@2026", bg=self.cores["superficie_2"], fg=self.cores["muted"], font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(0, 9))

        self.login_usuario.focus_set()
        self.root.bind("<Return>", self.autenticar_login)

    def alternar_visibilidade_senha(self):
        self.login_senha.configure(show="" if self.mostrar_senha_var.get() else "•")

    def autenticar_login(self, event=None):
        usuario = self.login_usuario.get().strip()
        senha = self.login_senha.get()
        if not usuario or not senha:
            self.lbl_login_erro.configure(text="Informe usuário e senha.")
            return

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, usuario, nome, senha_hash, salt FROM usuarios WHERE usuario = ? AND ativo = 1", (usuario,))
        registro = cur.fetchone()
        conn.close()

        valido = False
        if registro:
            calculado = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(registro[4]), 120000).hex()
            valido = hmac.compare_digest(calculado, registro[3])

        if not valido:
            self.lbl_login_erro.configure(text="Usuário ou senha inválidos.")
            self.login_senha.delete(0, tk.END)
            return

        self.usuario_atual = {"id": registro[0], "usuario": registro[1], "nome": registro[2]}
        self.root.unbind("<Return>")
        for w in self.root.winfo_children():
            w.destroy()
        self.criar_interface()
        self.atualizar_tudo()

    def sair(self):
        self.usuario_atual = None
        self.criar_tela_login()

    def criar_card(self, parent, titulo, valor, cor_fundo, cor_destaque, sigla):
        card = tk.Frame(
            parent,
            bg=cor_fundo,
            highlightthickness=1,
            highlightbackground=self.cores["borda"]
        )
        card.grid_propagate(False)
        card.columnconfigure(1, weight=1)

        badge = tk.Frame(card, bg=cor_destaque, width=46, height=46)
        badge.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=16, sticky="n")
        badge.grid_propagate(False)
        tk.Label(
            badge, text=sigla, bg=cor_destaque, fg="#FFFFFF",
            font=("Segoe UI Semibold", 11)
        ).place(relx=.5, rely=.5, anchor="center")

        tk.Label(
            card, text=titulo.upper(), bg=cor_fundo, fg=self.cores["muted"],
            font=("Segoe UI Semibold", 8)
        ).grid(row=0, column=1, sticky="sw", pady=(17, 0), padx=(0, 14))
        label_valor = tk.Label(
            card, text=valor, bg=cor_fundo, fg=self.cores["texto"],
            font=("Segoe UI Semibold", 26)
        )
        label_valor.grid(row=1, column=1, sticky="nw", pady=(0, 14), padx=(0, 14))
        return card, label_valor

    def criar_painel(self, parent, titulo, subtitulo=None, destaque=False):
        borda = self.cores["ambar"] if destaque else self.cores["borda"]
        painel = tk.Frame(
            parent, bg=self.cores["superficie"],
            highlightthickness=1, highlightbackground=borda
        )
        cab = tk.Frame(painel, bg=self.cores["superficie"])
        cab.pack(fill="x", padx=20, pady=(17, 10))
        tk.Label(
            cab, text=titulo, bg=self.cores["superficie"], fg=self.cores["texto"],
            font=("Segoe UI Semibold", 12)
        ).pack(anchor="w")
        if subtitulo:
            tk.Label(
                cab, text=subtitulo, bg=self.cores["superficie"], fg=self.cores["muted"],
                font=("Segoe UI", 9)
            ).pack(anchor="w", pady=(3, 0))
        return painel

    def criar_interface(self):
        self.vcmd_decimal = (self.root.register(self.validar_decimal), "%P")
        self.vcmd_inteiro = (self.root.register(self.validar_inteiro), "%P")

        self.root.title("BeerFlow • Gestão de Barris")
        self.root.geometry("1220x790")
        self.root.minsize(1050, 680)
        self.root.configure(bg=self.cores["fundo"])

        app = tk.Frame(self.root, bg=self.cores["fundo"])
        app.pack(fill="both", expand=True)

        # Menu lateral
        sidebar = tk.Frame(app, bg=self.cores["sidebar"], width=224)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=self.cores["sidebar"])
        brand.pack(fill="x", padx=20, pady=(24, 26))
        mark = tk.Frame(brand, bg=self.cores["ambar"], width=42, height=42)
        mark.pack(side="left", padx=(0, 11))
        mark.pack_propagate(False)
        tk.Label(mark, text="BF", bg=self.cores["ambar"], fg="#FFFFFF", font=("Segoe UI Semibold", 14)).pack(expand=True)
        brand_text = tk.Frame(brand, bg=self.cores["sidebar"])
        brand_text.pack(side="left", fill="x", expand=True)
        tk.Label(brand_text, text="BeerFlow", bg=self.cores["sidebar"], fg="#FFFFFF", font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(brand_text, text="GESTÃO DE BARRIS", bg=self.cores["sidebar"], fg="#9E938A", font=("Segoe UI Semibold", 7)).pack(anchor="w", pady=(2, 0))

        tk.Label(sidebar, text="NAVEGAÇÃO", bg=self.cores["sidebar"], fg="#71675F", font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=22, pady=(0, 8))

        self.nav_botoes = {}
        nav_items = [
            ("barris", "▦  Estoque"),
            ("adicionar", "+   Adicionar barris"),
            ("vendas", "▤  Vendas"),
            ("alertas", "!   Alertas"),
            ("relatorio", "≡  Relatório"),
        ]
        for chave, texto in nav_items:
            btn = tk.Button(
                sidebar, text=texto, anchor="w",
                bg=self.cores["sidebar"], fg="#CEC5BD",
                activebackground=self.cores["sidebar_2"], activeforeground="#FFFFFF",
                font=("Segoe UI Semibold", 10),
                bd=0, relief="flat", cursor="hand2",
                padx=20, pady=12,
                command=lambda c=chave: self.mostrar_aba(c)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_botoes[chave] = btn

        footer = tk.Frame(sidebar, bg=self.cores["sidebar"])
        footer.pack(side="bottom", fill="x", padx=16, pady=18)

        conta = tk.Frame(footer, bg=self.cores["sidebar_2"], highlightthickness=1, highlightbackground="#3A312B")
        conta.pack(fill="x", pady=(0, 8))
        avatar = tk.Frame(conta, bg=self.cores["ambar"], width=34, height=34)
        avatar.pack(side="left", padx=(10, 9), pady=10)
        avatar.pack_propagate(False)
        iniciais = "AD"
        if self.usuario_atual and self.usuario_atual.get("nome"):
            partes = self.usuario_atual["nome"].split()
            iniciais = "".join(p[0] for p in partes[:2]).upper()
        tk.Label(avatar, text=iniciais, bg=self.cores["ambar"], fg="#FFFFFF", font=("Segoe UI Semibold", 9)).pack(expand=True)
        dados = tk.Frame(conta, bg=self.cores["sidebar_2"])
        dados.pack(side="left", fill="x", expand=True, pady=9)
        tk.Label(dados, text=(self.usuario_atual or {}).get("nome", "Usuário"), bg=self.cores["sidebar_2"], fg="#FFFFFF", font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(dados, text="Sessão ativa", bg=self.cores["sidebar_2"], fg="#8FCDAA", font=("Segoe UI", 7)).pack(anchor="w", pady=(2, 0))
        tk.Button(conta, text="Sair", command=self.sair, bg=self.cores["sidebar_2"], fg="#BEB4AC", activebackground="#3A312B", activeforeground="#FFFFFF", bd=0, font=("Segoe UI", 8), cursor="hand2").pack(side="right", padx=9)

        status = tk.Frame(footer, bg=self.cores["sidebar"])
        status.pack(fill="x")
        tk.Label(status, text="●", bg=self.cores["sidebar"], fg="#65B88A", font=("Segoe UI", 9)).pack(side="left", padx=(4, 6), pady=4)
        tk.Label(status, text="Banco local conectado", bg=self.cores["sidebar"], fg="#8F857D", font=("Segoe UI", 7)).pack(side="left", pady=4)

        # Área principal
        main = tk.Frame(app, bg=self.cores["fundo"])
        main.pack(side="left", fill="both", expand=True)

        topbar = tk.Frame(main, bg=self.cores["superficie"], height=78, highlightthickness=1, highlightbackground=self.cores["borda"])
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        heading = tk.Frame(topbar, bg=self.cores["superficie"])
        heading.pack(side="left", fill="y", padx=28, pady=14)
        self.lbl_page_title = tk.Label(heading, text="Estoque", bg=self.cores["superficie"], fg=self.cores["texto"], font=("Segoe UI Semibold", 18))
        self.lbl_page_title.pack(anchor="w")
        self.lbl_page_subtitle = tk.Label(heading, text="Visão geral dos barris cadastrados", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI", 9))
        self.lbl_page_subtitle.pack(anchor="w", pady=(2, 0))

        chip = tk.Frame(topbar, bg=self.cores["ambar_claro"])
        chip.pack(side="right", padx=28, pady=22)
        tk.Label(chip, text="BEERFLOW", bg=self.cores["ambar_claro"], fg=self.cores["ambar_escuro"], font=("Segoe UI Semibold", 8)).pack(padx=11, pady=6)

        self.conteudo_paginas = tk.Frame(main, bg=self.cores["fundo"])
        self.conteudo_paginas.pack(fill="both", expand=True, padx=26, pady=20)

        self.aba_barris = tk.Frame(self.conteudo_paginas, bg=self.cores["fundo"])
        self.aba_adicionar_barris = tk.Frame(self.conteudo_paginas, bg=self.cores["fundo"])
        self.aba_vendas = tk.Frame(self.conteudo_paginas, bg=self.cores["fundo"])
        self.aba_alertas = tk.Frame(self.conteudo_paginas, bg=self.cores["fundo"])
        self.aba_relatorio = tk.Frame(self.conteudo_paginas, bg=self.cores["fundo"])
        self.paginas = {
            "barris": self.aba_barris,
            "adicionar": self.aba_adicionar_barris,
            "vendas": self.aba_vendas,
            "alertas": self.aba_alertas,
            "relatorio": self.aba_relatorio,
        }
        self.meta_paginas = {
            "barris": ("Estoque", "Visão geral dos barris e volumes disponíveis"),
            "adicionar": ("Adicionar barris", "Adicione novas unidades e acompanhe o estoque atual"),
            "vendas": ("Vendas", "Registre copos padrão ou volumes personalizados"),
            "alertas": ("Alertas", "Acompanhe níveis críticos e barris esgotados"),
            "relatorio": ("Relatório", "Indicadores consolidados do BeerFlow"),
        }

        self.montar_aba_barris()
        self.montar_aba_adicionar_barris()
        self.montar_aba_vendas()
        self.montar_aba_alertas()
        self.montar_aba_relatorio()
        self.mostrar_aba("barris")

    def mostrar_aba(self, chave):
        for pagina in self.paginas.values():
            pagina.pack_forget()
        self.paginas[chave].pack(fill="both", expand=True)

        for key, btn in self.nav_botoes.items():
            if key == chave:
                btn.configure(bg=self.cores["sidebar_2"], fg="#FFFFFF")
            else:
                btn.configure(bg=self.cores["sidebar"], fg="#CEC5BD")

        titulo, subtitulo = self.meta_paginas[chave]
        self.lbl_page_title.configure(text=titulo)
        self.lbl_page_subtitle.configure(text=subtitulo)

    def montar_aba_barris(self):
        cards = tk.Frame(self.aba_barris, bg=self.cores["fundo"])
        cards.pack(fill="x", pady=(0, 14))
        for i in range(3):
            cards.columnconfigure(i, weight=1, uniform="cards")

        card_cheios, self.lbl_barris_cheios = self.criar_card(cards, "Barris cheios", "0", self.cores["verde_claro"], self.cores["verde"], "OK")
        card_parciais, self.lbl_barris_parciais = self.criar_card(cards, "Em consumo", "0", self.cores["ambar_claro"], self.cores["ambar"], "ML")
        card_vazios, self.lbl_barris_vazios = self.criar_card(cards, "Barris vazios", "0", self.cores["vermelho_claro"], self.cores["vermelho"], "0L")
        card_cheios.grid(row=0, column=0, sticky="ew", padx=(0, 7))
        card_parciais.grid(row=0, column=1, sticky="ew", padx=7)
        card_vazios.grid(row=0, column=2, sticky="ew", padx=(7, 0))

        form = self.criar_painel(self.aba_barris, "Cadastrar novo barril", "Crie um novo tipo de cerveja e informe o volume inicial.")
        form.pack(fill="x", pady=(0, 14))
        campos = tk.Frame(form, bg=self.cores["superficie"])
        campos.pack(fill="x", padx=20, pady=(2, 18))
        campos.columnconfigure(1, weight=2)
        campos.columnconfigure(3, weight=1)

        tk.Label(campos, text="CERVEJA", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        self.nome_cerveja = ttk.Entry(campos)
        self.nome_cerveja.grid(row=0, column=1, padx=(0, 18), pady=6, sticky="ew")

        tk.Label(campos, text="VOLUME (L)", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).grid(row=0, column=2, padx=(0, 8), pady=6, sticky="w")
        self.volume_barril = ttk.Entry(campos, validate="key", validatecommand=self.vcmd_decimal)
        self.volume_barril.grid(row=0, column=3, padx=(0, 14), pady=6, sticky="ew")

        ttk.Button(campos, text="+  Cadastrar barril", style="Primary.TButton", command=self.cadastrar_barril).grid(row=0, column=4, pady=6, sticky="e")

        filtros_estoque = self.criar_painel(
            self.aba_barris,
            "Pesquisar no estoque",
            "Localize barris por ID, cerveja ou situação atual.",
            destaque=True
        )
        filtros_estoque.pack(fill="x", pady=(0, 14))

        filtro_grid = tk.Frame(filtros_estoque, bg=self.cores["superficie"])
        filtro_grid.pack(fill="x", padx=20, pady=(2, 16))
        filtro_grid.columnconfigure(0, weight=2)
        filtro_grid.columnconfigure(1, weight=1)
        filtro_grid.columnconfigure(2, weight=1)

        bloco_busca = tk.Frame(filtro_grid, bg=self.cores["superficie"])
        bloco_busca.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(bloco_busca, text="BUSCAR POR ID OU CERVEJA", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        self.estoque_busca = ttk.Entry(bloco_busca)
        self.estoque_busca.pack(fill="x")
        self.estoque_busca.bind("<KeyRelease>", lambda event: self.atualizar_barris())

        bloco_cerveja = tk.Frame(filtro_grid, bg=self.cores["superficie"])
        bloco_cerveja.grid(row=0, column=1, sticky="ew", padx=8)
        tk.Label(bloco_cerveja, text="CERVEJA", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        self.estoque_filtro_cerveja = ttk.Combobox(bloco_cerveja, state="readonly", values=("Todas",))
        self.estoque_filtro_cerveja.pack(fill="x")
        self.estoque_filtro_cerveja.set("Todas")
        self.estoque_filtro_cerveja.bind("<<ComboboxSelected>>", lambda event: self.atualizar_barris())

        bloco_status = tk.Frame(filtro_grid, bg=self.cores["superficie"])
        bloco_status.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        tk.Label(bloco_status, text="STATUS", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        self.estoque_filtro_status = ttk.Combobox(
            bloco_status,
            state="readonly",
            values=("Todos", "Cheio", "Em consumo", "Nível crítico", "Vazio")
        )
        self.estoque_filtro_status.pack(fill="x")
        self.estoque_filtro_status.set("Todos")
        self.estoque_filtro_status.bind("<<ComboboxSelected>>", lambda event: self.atualizar_barris())

        filtro_acoes = tk.Frame(filtros_estoque, bg=self.cores["superficie"])
        filtro_acoes.pack(fill="x", padx=20, pady=(0, 16))
        ttk.Button(filtro_acoes, text="Limpar filtros", style="Secondary.TButton", command=self.limpar_filtros_estoque).pack(side="left")
        self.lbl_estoque_resultados = tk.Label(
            filtro_acoes, text="", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI", 8)
        )
        self.lbl_estoque_resultados.pack(side="right")

        tabela_painel = self.criar_painel(self.aba_barris, "Barris cadastrados", "Acompanhe o volume disponível e o status de cada unidade.")
        tabela_painel.pack(fill="both", expand=True)
        tabela_frame = tk.Frame(tabela_painel, bg=self.cores["superficie"])
        tabela_frame.pack(fill="both", expand=True, padx=20, pady=(0, 18))

        colunas = ("id", "cerveja", "total", "atual", "status")
        self.tabela_barris = ttk.Treeview(tabela_frame, columns=colunas, show="headings", height=11)
        titulos = {"id": "ID", "cerveja": "CERVEJA", "total": "VOLUME TOTAL", "atual": "DISPONÍVEL", "status": "STATUS"}
        larguras = {"id": 70, "cerveja": 260, "total": 140, "atual": 140, "status": 210}
        for col in colunas:
            self.tabela_barris.heading(col, text=titulos[col])
            self.tabela_barris.column(col, width=larguras[col], anchor="center")
        self.tabela_barris.column("cerveja", anchor="w")
        self.tabela_barris.tag_configure("cheio", background="#F2FAF5")
        self.tabela_barris.tag_configure("parcial", background="#FFFBF4")
        self.tabela_barris.tag_configure("critico", background="#FFF3E6")
        self.tabela_barris.tag_configure("vazio", background="#FDF3F2")
        scroll = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tabela_barris.yview)
        self.tabela_barris.configure(yscrollcommand=scroll.set)
        self.tabela_barris.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def montar_aba_adicionar_barris(self):
        # Formulário de entrada de barris já cadastrados.
        # A antiga faixa "Entrada rápida de estoque" foi removida para deixar
        # a tela mais limpa e abrir espaço para a visão do estoque atual.
        frame = self.criar_painel(
            self.aba_adicionar_barris,
            "Adicionar ao estoque",
            "Inclua novas unidades de uma cerveja já registrada. Cada barril recebe um ID próprio.",
            destaque=True
        )
        frame.pack(fill="x", pady=(0, 14))
        campos = tk.Frame(frame, bg=self.cores["superficie"])
        campos.pack(fill="x", padx=20, pady=(6, 20))
        for i in range(3):
            campos.columnconfigure(i, weight=1, uniform="form")

        bloco1 = tk.Frame(campos, bg=self.cores["superficie"])
        bloco1.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Label(bloco1, text="CERVEJA REGISTRADA", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        self.combo_cerveja_existente = ttk.Combobox(bloco1, state="readonly")
        self.combo_cerveja_existente.pack(fill="x")

        bloco2 = tk.Frame(campos, bg=self.cores["superficie"])
        bloco2.grid(row=0, column=1, sticky="ew", padx=8)
        tk.Label(bloco2, text="VOLUME DE CADA BARRIL (L)", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        self.volume_novos_barris = ttk.Entry(bloco2, validate="key", validatecommand=self.vcmd_decimal)
        self.volume_novos_barris.pack(fill="x")

        bloco3 = tk.Frame(campos, bg=self.cores["superficie"])
        bloco3.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        tk.Label(bloco3, text="QUANTIDADE", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        self.quantidade_novos_barris = ttk.Spinbox(bloco3, from_=1, to=999, validate="key", validatecommand=self.vcmd_inteiro)
        self.quantidade_novos_barris.set("1")
        self.quantidade_novos_barris.pack(fill="x")

        ttk.Button(
            campos,
            text="+  Adicionar barris ao estoque",
            style="Primary.TButton",
            command=self.adicionar_barris_existentes
        ).grid(row=1, column=0, columnspan=3, pady=(16, 0), sticky="w")

        # Resumo do estoque também dentro desta aba.
        cards = tk.Frame(self.aba_adicionar_barris, bg=self.cores["fundo"])
        cards.pack(fill="x", pady=(0, 14))
        for i in range(3):
            cards.columnconfigure(i, weight=1, uniform="cards_add")

        card_cheios, self.lbl_add_barris_cheios = self.criar_card(
            cards, "Barris cheios", "0", self.cores["verde_claro"], self.cores["verde"], "OK"
        )
        card_parciais, self.lbl_add_barris_parciais = self.criar_card(
            cards, "Em consumo", "0", self.cores["ambar_claro"], self.cores["ambar"], "ML"
        )
        card_vazios, self.lbl_add_barris_vazios = self.criar_card(
            cards, "Barris vazios", "0", self.cores["vermelho_claro"], self.cores["vermelho"], "0L"
        )
        card_cheios.grid(row=0, column=0, sticky="ew", padx=(0, 7))
        card_parciais.grid(row=0, column=1, sticky="ew", padx=7)
        card_vazios.grid(row=0, column=2, sticky="ew", padx=(7, 0))

        estoque = self.criar_painel(
            self.aba_adicionar_barris,
            "Estoque atual",
            "Confira todos os barris cadastrados, o saldo disponível e o status de cada unidade."
        )
        estoque.pack(fill="both", expand=True)
        tabela_frame = tk.Frame(estoque, bg=self.cores["superficie"])
        tabela_frame.pack(fill="both", expand=True, padx=20, pady=(0, 18))

        colunas = ("id", "cerveja", "total", "atual", "status")
        self.tabela_barris_adicionar = ttk.Treeview(
            tabela_frame, columns=colunas, show="headings", height=8
        )
        titulos = {
            "id": "ID",
            "cerveja": "CERVEJA",
            "total": "VOLUME TOTAL",
            "atual": "DISPONÍVEL",
            "status": "STATUS",
        }
        larguras = {"id": 70, "cerveja": 260, "total": 140, "atual": 140, "status": 210}
        for col in colunas:
            self.tabela_barris_adicionar.heading(col, text=titulos[col])
            self.tabela_barris_adicionar.column(col, width=larguras[col], anchor="center")
        self.tabela_barris_adicionar.column("cerveja", anchor="w")
        self.tabela_barris_adicionar.tag_configure("cheio", background="#F2FAF5")
        self.tabela_barris_adicionar.tag_configure("parcial", background="#FFFBF4")
        self.tabela_barris_adicionar.tag_configure("critico", background="#FFF3E6")
        self.tabela_barris_adicionar.tag_configure("vazio", background="#FDF3F2")
        scroll = ttk.Scrollbar(
            tabela_frame, orient="vertical", command=self.tabela_barris_adicionar.yview
        )
        self.tabela_barris_adicionar.configure(yscrollcommand=scroll.set)
        self.tabela_barris_adicionar.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def montar_aba_vendas(self):
        corpo = tk.Frame(self.aba_vendas, bg=self.cores["fundo"])
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(0, weight=3)
        corpo.columnconfigure(1, weight=2)
        corpo.rowconfigure(0, weight=1)

        frame = self.criar_painel(corpo, "Nova venda", "Escolha um copo padrão ou informe um volume exato em mL.", destaque=True)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        campos = tk.Frame(frame, bg=self.cores["superficie"])
        campos.pack(fill="x", padx=20, pady=(5, 20))
        campos.columnconfigure(0, weight=1)

        tk.Label(campos, text="BARRIL", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.combo_barril = ttk.Combobox(campos, state="readonly")
        self.combo_barril.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        self.combo_barril.bind("<<ComboboxSelected>>", self.atualizar_estado_botao_limpeza)

        tk.Label(campos, text="TAMANHO DA VENDA", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.combo_tamanho_copo = ttk.Combobox(campos, state="readonly", values=("300 ml", "400 ml", "500 ml", "1 L", "Quantidade específica (ml)"))
        self.combo_tamanho_copo.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        self.combo_tamanho_copo.current(0)
        self.combo_tamanho_copo.bind("<<ComboboxSelected>>", self.atualizar_campo_ml_especifico)

        tk.Label(campos, text="VOLUME PERSONALIZADO (mL)", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 8)).grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.ml_especificos = ttk.Entry(campos, validate="key", validatecommand=self.vcmd_inteiro, state="disabled")
        self.ml_especificos.grid(row=5, column=0, sticky="ew")
        self.lbl_ml_especificos_info = tk.Label(campos, text="Habilitado ao selecionar “Quantidade específica (ml)”.", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI", 8))
        self.lbl_ml_especificos_info.grid(row=6, column=0, pady=(5, 16), sticky="w")

        botoes = tk.Frame(campos, bg=self.cores["superficie"])
        botoes.grid(row=7, column=0, sticky="ew")
        ttk.Button(botoes, text="✓  Registrar venda", style="Primary.TButton", command=self.registrar_venda).pack(side="left", padx=(0, 8))
        self.btn_limpar_barril = ttk.Button(botoes, text="Limpar barril", style="Danger.TButton", command=self.limpar_barril, state="disabled")
        self.btn_limpar_barril.pack(side="left")

        aviso = tk.Frame(frame, bg=self.cores["ambar_claro"])
        aviso.pack(fill="x", padx=20, pady=(0, 20))
        tk.Label(aviso, text="LIMPEZA SEGURA", bg=self.cores["ambar_claro"], fg=self.cores["ambar_escuro"], font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=13, pady=(11, 3))
        tk.Label(aviso, text="A limpeza só é liberada quando restam menos de 1,5 L. O descarte não entra como venda nem consumo.", bg=self.cores["ambar_claro"], fg=self.cores["texto"], font=("Segoe UI", 9), wraplength=560, justify="left").pack(anchor="w", padx=13, pady=(0, 11))

        resultado = tk.Frame(corpo, bg=self.cores["sidebar"], highlightthickness=1, highlightbackground="#3A312B")
        resultado.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(resultado, text="ÚLTIMA OPERAÇÃO", bg=self.cores["sidebar"], fg=self.cores["ambar"], font=("Segoe UI Semibold", 8)).pack(anchor="w", padx=22, pady=(22, 7))
        tk.Label(resultado, text="Resumo da movimentação", bg=self.cores["sidebar"], fg="#FFFFFF", font=("Segoe UI Semibold", 15)).pack(anchor="w", padx=22)
        self.lbl_resultado = tk.Label(
            resultado,
            text="Nenhuma operação realizada ainda.\n\nSelecione um barril e registre a primeira venda.",
            bg=self.cores["sidebar"], fg="#D8CFC7", font=("Segoe UI", 11),
            justify="left", anchor="nw", wraplength=320
        )
        self.lbl_resultado.pack(fill="both", expand=True, padx=22, pady=(24, 22), anchor="nw")

    def montar_aba_alertas(self):
        resumo = tk.Frame(self.aba_alertas, bg=self.cores["ambar_claro"], highlightthickness=1, highlightbackground="#F0D7B6")
        resumo.pack(fill="x", pady=(0, 14))
        tk.Label(resumo, text="!", bg=self.cores["ambar"], fg="#FFFFFF", font=("Segoe UI Semibold", 18), width=3).pack(side="left", fill="y")
        texto = tk.Frame(resumo, bg=self.cores["ambar_claro"])
        texto.pack(side="left", padx=16, pady=14)
        tk.Label(texto, text="Monitoramento automático", bg=self.cores["ambar_claro"], fg=self.cores["ambar_escuro"], font=("Segoe UI Semibold", 11)).pack(anchor="w")
        tk.Label(texto, text="O BeerFlow cria alertas quando o volume fica crítico ou quando um barril é esgotado.", bg=self.cores["ambar_claro"], fg=self.cores["texto"], font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))

        frame = self.criar_painel(self.aba_alertas, "Histórico de alertas", "Os 100 registros mais recentes aparecem primeiro.")
        frame.pack(fill="both", expand=True)
        tabela_frame = tk.Frame(frame, bg=self.cores["superficie"])
        tabela_frame.pack(fill="both", expand=True, padx=20, pady=(0, 18))

        colunas = ("data", "barril", "mensagem")
        self.tabela_alertas = ttk.Treeview(tabela_frame, columns=colunas, show="headings", height=16)
        self.tabela_alertas.heading("data", text="DATA / HORA")
        self.tabela_alertas.heading("barril", text="BARRIL")
        self.tabela_alertas.heading("mensagem", text="MENSAGEM")
        self.tabela_alertas.column("data", width=170, anchor="center")
        self.tabela_alertas.column("barril", width=110, anchor="center")
        self.tabela_alertas.column("mensagem", width=650, anchor="w")
        scroll = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tabela_alertas.yview)
        self.tabela_alertas.configure(yscrollcommand=scroll.set)
        self.tabela_alertas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def montar_aba_relatorio(self):
        tools = tk.Frame(self.aba_relatorio, bg=self.cores["fundo"])
        tools.pack(fill="x", pady=(0, 12))
        tk.Label(
            tools, text="Análise de vendas e desempenho do estoque",
            bg=self.cores["fundo"], fg=self.cores["muted"], font=("Segoe UI", 10)
        ).pack(side="left")
        ttk.Button(tools, text="Exportar CSV", style="Secondary.TButton", command=self.exportar_relatorio_csv).pack(side="right", padx=(8, 0))
        ttk.Button(
            tools,
            text="↻  Atualizar relatórios",
            style="Secondary.TButton",
            command=self.confirmar_atualizacao_relatorio
        ).pack(side="right")

        filtros = self.criar_painel(
            self.aba_relatorio, "Filtros inteligentes",
            "Cruze período, cerveja, barril e situação atual para montar a visão desejada.",
            destaque=True
        )
        filtros.pack(fill="x", pady=(0, 12))

        grid = tk.Frame(filtros, bg=self.cores["superficie"])
        grid.pack(fill="x", padx=20, pady=(0, 10))
        for i in range(6):
            grid.columnconfigure(i, weight=1, uniform="filtros_rel")

        def bloco(c, titulo):
            f = tk.Frame(grid, bg=self.cores["superficie"])
            f.grid(row=0, column=c, sticky="ew", padx=(0 if c == 0 else 5, 5 if c < 5 else 0))
            tk.Label(f, text=titulo, bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 7)).pack(anchor="w", pady=(0, 5))
            return f

        b_periodo = bloco(0, "PERÍODO")
        self.rel_periodo = ttk.Combobox(b_periodo, state="readonly", values=("Todo o período", "Hoje", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Personalizado"))
        self.rel_periodo.pack(fill="x")
        self.rel_periodo.current(0)
        self.rel_periodo.bind("<<ComboboxSelected>>", self.alterar_periodo_relatorio)

        b_cerveja = bloco(1, "CERVEJA")
        self.rel_cerveja = ttk.Combobox(b_cerveja, state="readonly", values=("Todas",))
        self.rel_cerveja.pack(fill="x")
        self.rel_cerveja.set("Todas")
        self.rel_cerveja.bind("<<ComboboxSelected>>", self.atualizar_combo_relatorio_barris)

        b_barril = bloco(2, "BARRIL")
        self.rel_barril = ttk.Combobox(b_barril, state="readonly", values=("Todos",))
        self.rel_barril.pack(fill="x")
        self.rel_barril.set("Todos")

        b_status = bloco(3, "STATUS ATUAL")
        self.rel_status = ttk.Combobox(b_status, state="readonly", values=("Todos", "Cheio", "Parcial", "Vazio"))
        self.rel_status.pack(fill="x")
        self.rel_status.current(0)

        b_inicio = bloco(4, "DATA INICIAL")
        self.rel_data_inicio = ttk.Entry(b_inicio)
        self.rel_data_inicio.pack(fill="x")
        self.rel_data_inicio.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.rel_data_inicio.configure(state="disabled")

        b_fim = bloco(5, "DATA FINAL")
        self.rel_data_fim = ttk.Entry(b_fim)
        self.rel_data_fim.pack(fill="x")
        self.rel_data_fim.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.rel_data_fim.configure(state="disabled")

        acoes = tk.Frame(filtros, bg=self.cores["superficie"])
        acoes.pack(fill="x", padx=20, pady=(0, 16))
        ttk.Button(acoes, text="Aplicar filtros", style="Primary.TButton", command=self.atualizar_relatorio).pack(side="left")
        ttk.Button(acoes, text="Limpar filtros", style="Secondary.TButton", command=self.limpar_filtros_relatorio).pack(side="left", padx=(8, 0))
        self.lbl_rel_filtro_ativo = tk.Label(acoes, text="Exibindo todo o histórico", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI", 8))
        self.lbl_rel_filtro_ativo.pack(side="right")

        self.rel_notebook = ttk.Notebook(self.aba_relatorio, style="Reports.TNotebook")
        self.rel_notebook.pack(fill="both", expand=True)
        self.rel_visao = tk.Frame(self.rel_notebook, bg=self.cores["fundo"])
        self.rel_detalhe = tk.Frame(self.rel_notebook, bg=self.cores["fundo"])
        self.rel_notebook.add(self.rel_visao, text="  Visão geral  ")
        self.rel_notebook.add(self.rel_detalhe, text="  Vendas detalhadas  ")

        cards = tk.Frame(self.rel_visao, bg=self.cores["fundo"])
        cards.pack(fill="x", pady=(12, 12))
        for i in range(4):
            cards.columnconfigure(i, weight=1, uniform="relcards")
        c1, self.lbl_rel_vendas = self.criar_card(cards, "Vendas", "0", self.cores["azul_claro"], self.cores["azul"], "VD")
        c2, self.lbl_rel_litros = self.criar_card(cards, "Litros vendidos", "0,00 L", self.cores["verde_claro"], self.cores["verde"], "L")
        c3, self.lbl_rel_media = self.criar_card(cards, "Média por venda", "0 mL", self.cores["ambar_claro"], self.cores["ambar"], "ML")
        c4, self.lbl_rel_barris = self.criar_card(cards, "Barris envolvidos", "0", self.cores["vermelho_claro"], self.cores["vermelho"], "BR")
        c1.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        c2.grid(row=0, column=1, sticky="ew", padx=5)
        c3.grid(row=0, column=2, sticky="ew", padx=5)
        c4.grid(row=0, column=3, sticky="ew", padx=(5, 0))

        destaques = tk.Frame(self.rel_visao, bg=self.cores["fundo"])
        destaques.pack(fill="x", pady=(0, 12))
        destaques.columnconfigure(0, weight=1)
        destaques.columnconfigure(1, weight=1)
        destaques.columnconfigure(2, weight=1)

        self.rel_kpi_top = self._criar_kpi_compacto(destaques, 0, "CERVEJA MAIS VENDIDA", "—", self.cores["ambar"])
        self.rel_kpi_maior = self._criar_kpi_compacto(destaques, 1, "MAIOR VENDA", "—", self.cores["azul"])
        self.rel_kpi_disponivel = self._criar_kpi_compacto(destaques, 2, "ESTOQUE DISPONÍVEL", "0,00 L", self.cores["verde"])

        analise = tk.Frame(self.rel_visao, bg=self.cores["fundo"])
        analise.pack(fill="both", expand=True)
        analise.columnconfigure(0, weight=3)
        analise.columnconfigure(1, weight=2)
        analise.rowconfigure(0, weight=1)

        graf = self.criar_painel(analise, "Evolução das vendas", "Volume vendido por dia dentro do filtro selecionado.")
        graf.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.rel_canvas_grafico = tk.Canvas(graf, bg=self.cores["superficie"], highlightthickness=0, height=230)
        self.rel_canvas_grafico.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        direita = tk.Frame(analise, bg=self.cores["fundo"])
        direita.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        direita.rowconfigure(0, weight=1)
        direita.columnconfigure(0, weight=1)

        ranking = self.criar_painel(direita, "Ranking por cerveja", "Participação no volume vendido.")
        ranking.grid(row=0, column=0, sticky="nsew")
        self.frame_ranking_relatorio = tk.Frame(ranking, bg=self.cores["superficie"])
        self.frame_ranking_relatorio.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        cab_detalhe = tk.Frame(self.rel_detalhe, bg=self.cores["fundo"])
        cab_detalhe.pack(fill="x", pady=(12, 8))
        tk.Label(cab_detalhe, text="Vendas encontradas", bg=self.cores["fundo"], fg=self.cores["texto"], font=("Segoe UI Semibold", 14)).pack(side="left")
        self.lbl_rel_qtd_linhas = tk.Label(cab_detalhe, text="0 registros", bg=self.cores["fundo"], fg=self.cores["muted"], font=("Segoe UI", 9))
        self.lbl_rel_qtd_linhas.pack(side="right")

        detalhe = self.criar_painel(self.rel_detalhe, "Detalhamento", "Histórico completo das vendas que correspondem aos filtros aplicados.")
        detalhe.pack(fill="both", expand=True)
        tabela_frame = tk.Frame(detalhe, bg=self.cores["superficie"])
        tabela_frame.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        colunas = ("data", "barril", "cerveja", "volume", "categoria")
        self.tabela_relatorio = ttk.Treeview(tabela_frame, columns=colunas, show="headings", height=14)
        titulos = {"data":"DATA / HORA", "barril":"BARRIL", "cerveja":"CERVEJA", "volume":"VOLUME", "categoria":"TIPO"}
        larguras = {"data":160, "barril":90, "cerveja":250, "volume":120, "categoria":150}
        for col in colunas:
            self.tabela_relatorio.heading(col, text=titulos[col])
            self.tabela_relatorio.column(col, width=larguras[col], anchor="center")
        self.tabela_relatorio.column("cerveja", anchor="w")
        scroll = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tabela_relatorio.yview)
        self.tabela_relatorio.configure(yscrollcommand=scroll.set)
        self.tabela_relatorio.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.relatorio_linhas_exportacao = []

    def _criar_kpi_compacto(self, parent, coluna, titulo, valor, cor):
        frame = tk.Frame(parent, bg=self.cores["superficie"], highlightthickness=1, highlightbackground=self.cores["borda"])
        frame.grid(row=0, column=coluna, sticky="ew", padx=(0 if coluna == 0 else 5, 0 if coluna == 2 else 5))
        faixa = tk.Frame(frame, bg=cor, width=5)
        faixa.pack(side="left", fill="y")
        corpo = tk.Frame(frame, bg=self.cores["superficie"])
        corpo.pack(side="left", fill="both", expand=True, padx=14, pady=12)
        tk.Label(corpo, text=titulo, bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI Semibold", 7)).pack(anchor="w")
        lbl = tk.Label(corpo, text=valor, bg=self.cores["superficie"], fg=self.cores["texto"], font=("Segoe UI Semibold", 13))
        lbl.pack(anchor="w", pady=(3, 0))
        return lbl

    def alterar_periodo_relatorio(self, event=None):
        personalizado = self.rel_periodo.get() == "Personalizado"
        estado = "normal" if personalizado else "disabled"
        self.rel_data_inicio.configure(state=estado)
        self.rel_data_fim.configure(state=estado)
        if not personalizado:
            self.atualizar_relatorio()

    def limpar_filtros_relatorio(self):
        self.rel_periodo.set("Todo o período")
        self.rel_cerveja.set("Todas")
        self.rel_barril.set("Todos")
        self.rel_status.set("Todos")
        self.rel_data_inicio.configure(state="normal")
        self.rel_data_fim.configure(state="normal")
        hoje = datetime.now().strftime("%d/%m/%Y")
        self.rel_data_inicio.delete(0, tk.END)
        self.rel_data_inicio.insert(0, hoje)
        self.rel_data_fim.delete(0, tk.END)
        self.rel_data_fim.insert(0, hoje)
        self.rel_data_inicio.configure(state="disabled")
        self.rel_data_fim.configure(state="disabled")
        self.atualizar_combo_relatorio_barris()
        self.atualizar_relatorio()

    def obter_intervalo_relatorio(self):
        agora = datetime.now()
        hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        periodo = self.rel_periodo.get() if hasattr(self, "rel_periodo") else "Todo o período"
        if periodo == "Todo o período":
            return None, None
        if periodo == "Hoje":
            return hoje, hoje + timedelta(days=1)
        if periodo == "Últimos 7 dias":
            return hoje - timedelta(days=6), hoje + timedelta(days=1)
        if periodo == "Últimos 30 dias":
            return hoje - timedelta(days=29), hoje + timedelta(days=1)
        if periodo == "Este mês":
            inicio = hoje.replace(day=1)
            fim = inicio.replace(year=inicio.year + 1, month=1) if inicio.month == 12 else inicio.replace(month=inicio.month + 1)
            return inicio, fim
        if periodo == "Personalizado":
            try:
                inicio = datetime.strptime(self.rel_data_inicio.get().strip(), "%d/%m/%Y")
                fim_dia = datetime.strptime(self.rel_data_fim.get().strip(), "%d/%m/%Y")
                if fim_dia < inicio:
                    raise ValueError
                return inicio, fim_dia + timedelta(days=1)
            except ValueError:
                messagebox.showwarning("Filtro inválido", "Use datas no formato DD/MM/AAAA e mantenha a data final igual ou posterior à inicial.")
                return False, False
        return None, None

    def atualizar_combo_relatorio_cervejas(self):
        if not hasattr(self, "rel_cerveja"):
            return
        atual = self.rel_cerveja.get() or "Todas"
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT nome FROM cervejas ORDER BY nome")
        valores = ["Todas"] + [r[0] for r in cur.fetchall()]
        conn.close()
        self.rel_cerveja["values"] = valores
        self.rel_cerveja.set(atual if atual in valores else "Todas")
        self.atualizar_combo_relatorio_barris()

    def atualizar_combo_relatorio_barris(self, event=None):
        if not hasattr(self, "rel_barril"):
            return
        atual = self.rel_barril.get() or "Todos"
        cerveja = self.rel_cerveja.get() if hasattr(self, "rel_cerveja") else "Todas"
        conn = conectar()
        cur = conn.cursor()
        if cerveja and cerveja != "Todas":
            cur.execute("""SELECT b.id, c.nome FROM barris b JOIN cervejas c ON c.id=b.cerveja_id WHERE c.nome=? ORDER BY b.id""", (cerveja,))
        else:
            cur.execute("""SELECT b.id, c.nome FROM barris b JOIN cervejas c ON c.id=b.cerveja_id ORDER BY b.id""")
        valores = ["Todos"] + [f"#{bid} • {nome}" for bid, nome in cur.fetchall()]
        conn.close()
        self.rel_barril["values"] = valores
        self.rel_barril.set(atual if atual in valores else "Todos")

    def exportar_relatorio_csv(self):
        if not getattr(self, "relatorio_linhas_exportacao", None):
            messagebox.showinfo("Relatório", "Não há vendas no filtro atual para exportar.")
            return
        caminho = filedialog.asksaveasfilename(
            title="Exportar relatório", defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv")],
            initialfile=f"beerflow_relatorio_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        )
        if not caminho:
            return
        with open(caminho, "w", newline="", encoding="utf-8-sig") as arq:
            writer = csv.writer(arq, delimiter=";")
            writer.writerow(["Data/Hora", "Barril", "Cerveja", "Volume vendido (L)", "Volume vendido (mL)", "Tipo"])
            writer.writerows(self.relatorio_linhas_exportacao)
        messagebox.showinfo("Relatório exportado", "O arquivo CSV foi salvo com sucesso.")

    def classificar_tamanho_venda(self, litros):
        ml = round(litros * 1000)
        padroes = {300: "Copo 300 mL", 400: "Copo 400 mL", 500: "Copo 500 mL", 1000: "Copo 1 L"}
        return padroes.get(ml, "Personalizado")

    def desenhar_grafico_relatorio(self, dados):
        if not hasattr(self, "rel_canvas_grafico"):
            return
        canvas = self.rel_canvas_grafico
        canvas.delete("all")
        canvas.update_idletasks()
        w = max(canvas.winfo_width(), 480)
        h = max(canvas.winfo_height(), 220)
        if not dados:
            canvas.create_text(w/2, h/2, text="Sem vendas para exibir neste período", fill=self.cores["muted"], font=("Segoe UI", 10))
            return
        itens = sorted(dados.items())[-14:]
        maior = max(v for _, v in itens) or 1
        margem_x, margem_top, margem_bottom = 38, 18, 42
        area_h = h - margem_top - margem_bottom
        gap = 10
        slot = (w - 2*margem_x) / max(len(itens), 1)
        bar_w = max(12, min(34, slot - gap))
        canvas.create_line(margem_x, h-margem_bottom, w-margem_x, h-margem_bottom, fill=self.cores["borda_forte"])
        for i, (data, valor) in enumerate(itens):
            cx = margem_x + slot*i + slot/2
            bh = area_h * (valor/maior)
            x1, x2 = cx-bar_w/2, cx+bar_w/2
            y1, y2 = h-margem_bottom-bh, h-margem_bottom
            canvas.create_rectangle(x1, y1, x2, y2, fill=self.cores["ambar"], outline="")
            canvas.create_text(cx, max(y1-9, 9), text=f"{valor:.1f}L", fill=self.cores["texto"], font=("Segoe UI Semibold", 7))
            try:
                rotulo = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m")
            except ValueError:
                rotulo = data[-5:]
            canvas.create_text(cx, h-margem_bottom+16, text=rotulo, fill=self.cores["muted"], font=("Segoe UI", 7))

    def cadastrar_barril(self):
        nome = self.nome_cerveja.get().strip()
        volume_txt = self.volume_barril.get().strip().replace(",", ".")

        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome da cerveja.")
            return

        try:
            volume = float(volume_txt)
            if volume <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um volume válido.")
            return

        conn = conectar()
        cur = conn.cursor()

        cur.execute("SELECT id FROM cervejas WHERE nome = ?", (nome,))
        row = cur.fetchone()

        if row:
            cerveja_id = row[0]
        else:
            cur.execute("INSERT INTO cervejas (nome) VALUES (?)", (nome,))
            cerveja_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO barris (cerveja_id, volume_total, volume_atual, ativo)
            VALUES (?, ?, ?, 1)
            """,
            (cerveja_id, volume, volume)
        )

        conn.commit()
        conn.close()

        self.nome_cerveja.delete(0, tk.END)
        self.volume_barril.delete(0, tk.END)

        self.atualizar_tudo()
        messagebox.showinfo("Sucesso", "Barril cadastrado com sucesso.")

    def adicionar_barris_existentes(self):
        selecao = self.combo_cerveja_existente.get()
        volume_txt = self.volume_novos_barris.get().strip().replace(",", ".")
        quantidade_txt = self.quantidade_novos_barris.get().strip()

        if not selecao:
            messagebox.showwarning("Atenção", "Selecione uma cerveja já registrada.")
            return

        try:
            volume = float(volume_txt)
            if volume <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe um volume válido.")
            return

        try:
            quantidade = int(quantidade_txt)
            if quantidade <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe uma quantidade válida de barris.")
            return

        cerveja_id = int(selecao.split(" - ")[0])

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT nome FROM cervejas WHERE id = ?", (cerveja_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            messagebox.showerror("Erro", "Cerveja não encontrada.")
            return

        nome = row[0]
        cur.executemany(
            """
            INSERT INTO barris (cerveja_id, volume_total, volume_atual, ativo)
            VALUES (?, ?, ?, 1)
            """,
            [(cerveja_id, volume, volume) for _ in range(quantidade)]
        )
        conn.commit()
        conn.close()

        self.volume_novos_barris.delete(0, tk.END)
        self.quantidade_novos_barris.set("1")
        self.atualizar_tudo()
        messagebox.showinfo(
            "Sucesso",
            f"{quantidade} barril(is) de {nome} adicionado(s) com sucesso."
        )

    def atualizar_campo_ml_especifico(self, event=None):
        personalizado = self.combo_tamanho_copo.get() == "Quantidade específica (ml)"
        self.ml_especificos.config(state="normal" if personalizado else "disabled")
        if not personalizado:
            self.ml_especificos.delete(0, tk.END)

    def registrar_venda(self):
        selecao = self.combo_barril.get()
        tamanho_copo = self.combo_tamanho_copo.get()

        if not selecao:
            messagebox.showwarning("Atenção", "Selecione um barril.")
            return

        volumes_copo = {
            "300 ml": 0.3,
            "400 ml": 0.4,
            "500 ml": 0.5,
            "1 L": 1.0,
        }

        if tamanho_copo == "Quantidade específica (ml)":
            ml_txt = self.ml_especificos.get().strip()
            try:
                quantidade_ml = int(ml_txt)
                if quantidade_ml <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Atenção", "Informe uma quantidade válida em mL.")
                return
            quantidade_litros = quantidade_ml / 1000.0
            descricao_venda = f"{quantidade_ml} ml"
        else:
            quantidade_litros = volumes_copo.get(tamanho_copo)
            if quantidade_litros is None:
                messagebox.showwarning("Atenção", "Selecione a quantidade da venda.")
                return
            descricao_venda = tamanho_copo

        barril_id = int(selecao.split(" - ")[0])

        conn = conectar()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT b.volume_atual, c.nome
            FROM barris b
            JOIN cervejas c ON c.id = b.cerveja_id
            WHERE b.id = ? AND b.ativo = 1
            """,
            (barril_id,)
        )

        row = cur.fetchone()

        if not row:
            conn.close()
            messagebox.showerror("Erro", "Barril não encontrado ou inativo.")
            return

        volume_atual, cerveja_nome = row

        if quantidade_litros > volume_atual:
            conn.close()
            messagebox.showwarning(
                "Venda não permitida",
                f"O barril possui apenas {volume_atual:.2f} L disponíveis."
            )
            return

        novo_volume = volume_atual - quantidade_litros
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            """
            INSERT INTO vendas (barril_id, quantidade_litros, data_hora)
            VALUES (?, ?, ?)
            """,
            (barril_id, quantidade_litros, agora)
        )

        cur.execute(
            "UPDATE barris SET volume_atual = ? WHERE id = ?",
            (novo_volume, barril_id)
        )

        mensagem_alerta = None

        if novo_volume <= 0:
            mensagem_alerta = f"Barril #{barril_id} ({cerveja_nome}) esgotado. Troca necessária."
            cur.execute("UPDATE barris SET ativo = 0 WHERE id = ?", (barril_id,))
        elif novo_volume <= LIMITE_CRITICO_LITROS:
            mensagem_alerta = (
                f"Barril #{barril_id} ({cerveja_nome}) com baixo volume: "
                f"{novo_volume:.2f} L restantes."
            )

        if mensagem_alerta:
            cur.execute(
                """
                INSERT INTO alertas (barril_id, mensagem, data_hora)
                VALUES (?, ?, ?)
                """,
                (barril_id, mensagem_alerta, agora)
            )

        conn.commit()
        conn.close()

        texto = (
            f"Venda registrada com sucesso!\n\n"
            f"Cerveja: {cerveja_nome}\n"
            f"Volume vendido: {descricao_venda}\n"
            f"Volume restante: {novo_volume:.2f} L"
        )

        if mensagem_alerta:
            texto += f"\n\nALERTA: {mensagem_alerta}"
            messagebox.showwarning("Alerta BeerFlow", mensagem_alerta)

        self.lbl_resultado.config(text=texto)
        self.atualizar_tudo()

    def atualizar_estado_botao_limpeza(self, event=None):
        selecao = self.combo_barril.get()
        habilitar = False

        if selecao:
            try:
                barril_id = int(selecao.split(" - ")[0])
                conn = conectar()
                cur = conn.cursor()
                cur.execute(
                    "SELECT volume_atual FROM barris WHERE id = ? AND ativo = 1",
                    (barril_id,)
                )
                row = cur.fetchone()
                conn.close()
                if row:
                    volume_atual = row[0]
                    habilitar = 0.000001 < volume_atual < LIMITE_LIMPEZA_LITROS
            except (ValueError, sqlite3.Error):
                habilitar = False

        self.btn_limpar_barril.config(state="normal" if habilitar else "disabled")

    def limpar_barril(self):
        selecao = self.combo_barril.get()

        if not selecao:
            messagebox.showwarning("Atenção", "Selecione um barril.")
            return

        barril_id = int(selecao.split(" - ")[0])

        conn = conectar()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT b.volume_atual, c.nome
            FROM barris b
            JOIN cervejas c ON c.id = b.cerveja_id
            WHERE b.id = ? AND b.ativo = 1
            """,
            (barril_id,)
        )
        row = cur.fetchone()

        if not row:
            conn.close()
            messagebox.showerror("Erro", "Barril não encontrado ou já está vazio.")
            return

        volume_atual, cerveja_nome = row

        if volume_atual <= 0.000001:
            conn.close()
            messagebox.showinfo("Barril vazio", "Este barril já está vazio.")
            return

        if volume_atual >= LIMITE_LIMPEZA_LITROS - 0.000001:
            conn.close()
            messagebox.showwarning(
                "Limpeza não permitida",
                f"O barril ainda possui {volume_atual:.2f} L. "
                f"A limpeza só é permitida quando restarem menos de {LIMITE_LIMPEZA_LITROS:.1f} L."
            )
            return

        confirmar = messagebox.askyesno(
            "Limpar barril",
            f"O barril #{barril_id} ({cerveja_nome}) possui {volume_atual:.2f} L.\n\n"
            "Deseja zerar este volume? Esta operação NÃO será registrada como venda nem consumo."
        )
        if not confirmar:
            conn.close()
            return

        # A limpeza altera apenas o saldo do barril. Não cria registro em vendas,
        # portanto o volume descartado não entra no total vendido nem no consumo por cerveja.
        cur.execute(
            "UPDATE barris SET volume_atual = 0, ativo = 0 WHERE id = ?",
            (barril_id,)
        )
        conn.commit()
        conn.close()

        self.lbl_resultado.config(
            text=(
                f"Barril limpo com sucesso!\n\n"
                f"Barril: #{barril_id} - {cerveja_nome}\n"
                f"Volume zerado: {volume_atual:.2f} L\n"
                "Registro de venda/consumo: NÃO"
            )
        )
        self.atualizar_tudo()
        messagebox.showinfo("Sucesso", "Barril zerado sem registrar venda ou consumo.")

    def atualizar_tudo(self):
        self.atualizar_barris()
        self.atualizar_resumo_barris()
        self.atualizar_combo_cervejas()
        self.atualizar_combo_barris()
        self.atualizar_alertas()
        self.atualizar_relatorio()

    def limpar_filtros_estoque(self):
        if hasattr(self, "estoque_busca"):
            self.estoque_busca.delete(0, tk.END)
        if hasattr(self, "estoque_filtro_cerveja"):
            self.estoque_filtro_cerveja.set("Todas")
        if hasattr(self, "estoque_filtro_status"):
            self.estoque_filtro_status.set("Todos")
        self.atualizar_barris()

    def atualizar_barris(self):
        if hasattr(self, "tabela_barris"):
            for item in self.tabela_barris.get_children():
                self.tabela_barris.delete(item)
        if hasattr(self, "tabela_barris_adicionar"):
            for item in self.tabela_barris_adicionar.get_children():
                self.tabela_barris_adicionar.delete(item)

        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT b.id, c.nome, b.volume_total, b.volume_atual, b.ativo
            FROM barris b
            JOIN cervejas c ON c.id = b.cerveja_id
            ORDER BY b.id DESC
        """)
        rows = cur.fetchall()
        conn.close()

        busca = self.estoque_busca.get().strip().lower() if hasattr(self, "estoque_busca") else ""
        cerveja_filtro = self.estoque_filtro_cerveja.get() if hasattr(self, "estoque_filtro_cerveja") else "Todas"
        status_filtro = self.estoque_filtro_status.get() if hasattr(self, "estoque_filtro_status") else "Todos"
        encontrados = 0

        for barril_id, nome, total, atual, ativo in rows:
            if atual <= 0.000001:
                status = "Vazio"
                categoria_status = "Vazio"
            elif atual >= total - 0.000001:
                status = "Cheio"
                categoria_status = "Cheio"
            elif atual <= LIMITE_CRITICO_LITROS:
                status = "Parcial - nível crítico"
                categoria_status = "Nível crítico"
            else:
                status = "Parcialmente vendido"
                categoria_status = "Em consumo"

            if status == "Cheio":
                tag = "cheio"
            elif status == "Vazio":
                tag = "vazio"
            elif "crítico" in status:
                tag = "critico"
            else:
                tag = "parcial"

            valores = (
                barril_id,
                nome,
                f"{total:.2f} L",
                f"{atual:.2f} L",
                status
            )

            # A tabela da aba Adicionar barris continua exibindo o estoque completo.
            if hasattr(self, "tabela_barris_adicionar"):
                self.tabela_barris_adicionar.insert("", "end", values=valores, tags=(tag,))

            corresponde_busca = (
                not busca
                or busca in nome.lower()
                or busca in str(barril_id).lower()
                or busca in f"#{barril_id}".lower()
            )
            corresponde_cerveja = cerveja_filtro in ("", "Todas") or nome == cerveja_filtro
            if status_filtro in ("", "Todos"):
                corresponde_status = True
            elif status_filtro == "Em consumo":
                corresponde_status = categoria_status in ("Em consumo", "Nível crítico")
            else:
                corresponde_status = categoria_status == status_filtro

            if corresponde_busca and corresponde_cerveja and corresponde_status:
                if hasattr(self, "tabela_barris"):
                    self.tabela_barris.insert("", "end", values=valores, tags=(tag,))
                encontrados += 1

        if hasattr(self, "lbl_estoque_resultados"):
            total = len(rows)
            if encontrados == total and not busca and cerveja_filtro in ("", "Todas") and status_filtro in ("", "Todos"):
                texto = f"{total} {'barril' if total == 1 else 'barris'} no estoque"
            else:
                texto = f"{encontrados} de {total} {'barril' if total == 1 else 'barris'} encontrados"
            self.lbl_estoque_resultados.config(text=texto)

    def atualizar_resumo_barris(self):
        conn = conectar()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM barris WHERE volume_atual >= volume_total - 0.000001 AND volume_atual > 0")
        cheios = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM barris WHERE volume_atual > 0.000001 AND volume_atual < volume_total - 0.000001")
        parciais = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM barris WHERE volume_atual <= 0.000001")
        vazios = cur.fetchone()[0]
        conn.close()

        self.lbl_barris_cheios.config(text=str(cheios))
        self.lbl_barris_parciais.config(text=str(parciais))
        self.lbl_barris_vazios.config(text=str(vazios))

        if hasattr(self, "lbl_add_barris_cheios"):
            self.lbl_add_barris_cheios.config(text=str(cheios))
            self.lbl_add_barris_parciais.config(text=str(parciais))
            self.lbl_add_barris_vazios.config(text=str(vazios))

    def atualizar_combo_cervejas(self):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM cervejas ORDER BY nome")
        valores = [f"{cerveja_id} - {nome}" for cerveja_id, nome in cur.fetchall()]
        conn.close()

        self.combo_cerveja_existente["values"] = valores
        if valores:
            if self.combo_cerveja_existente.get() not in valores:
                self.combo_cerveja_existente.current(0)
        else:
            self.combo_cerveja_existente.set("")

        if hasattr(self, "estoque_filtro_cerveja"):
            nomes = [valor.split(" - ", 1)[1] for valor in valores]
            opcoes = ["Todas"] + nomes
            atual = self.estoque_filtro_cerveja.get() or "Todas"
            self.estoque_filtro_cerveja["values"] = opcoes
            self.estoque_filtro_cerveja.set(atual if atual in opcoes else "Todas")

    def atualizar_combo_barris(self):
        selecao_anterior = self.combo_barril.get()
        id_anterior = None
        if selecao_anterior:
            try:
                id_anterior = int(selecao_anterior.split(" - ")[0])
            except ValueError:
                id_anterior = None

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT b.id, c.nome, b.volume_atual
            FROM barris b
            JOIN cervejas c ON c.id = b.cerveja_id
            WHERE b.ativo = 1
            ORDER BY c.nome
        """)

        valores = [
            f"{barril_id} - {nome} - {volume:.2f} L"
            for barril_id, nome, volume in cur.fetchall()
        ]

        self.combo_barril["values"] = valores

        valor_preservado = next(
            (valor for valor in valores if id_anterior is not None and valor.startswith(f"{id_anterior} - ")),
            None
        )

        if valor_preservado:
            self.combo_barril.set(valor_preservado)
        elif valores:
            self.combo_barril.current(0)
        else:
            self.combo_barril.set("")

        conn.close()
        self.atualizar_estado_botao_limpeza()

    def atualizar_alertas(self):
        for item in self.tabela_alertas.get_children():
            self.tabela_alertas.delete(item)

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT a.data_hora, a.barril_id, a.mensagem
            FROM alertas a
            ORDER BY a.id DESC
            LIMIT 100
        """)

        for data_hora, barril_id, mensagem in cur.fetchall():
            self.tabela_alertas.insert(
                "",
                "end",
                values=(data_hora, f"#{barril_id}", mensagem)
            )

        conn.close()

    def confirmar_atualizacao_relatorio(self):
        confirmar = messagebox.askyesno(
            "Atualizar relatórios",
            "Deseja atualizar os relatórios agora?\n\n"
            "Os indicadores, o ranking e a tabela serão recarregados conforme os filtros atuais."
        )
        if confirmar:
            self.atualizar_relatorio()

    def atualizar_relatorio(self):
        if not hasattr(self, "tabela_relatorio"):
            return

        self.atualizar_combo_relatorio_cervejas()
        intervalo = self.obter_intervalo_relatorio()
        if intervalo == (False, False):
            return
        inicio, fim = intervalo

        where, params = [], []
        if inicio is not None:
            where.append("v.data_hora >= ?")
            params.append(inicio.strftime("%Y-%m-%d %H:%M:%S"))
        if fim is not None:
            where.append("v.data_hora < ?")
            params.append(fim.strftime("%Y-%m-%d %H:%M:%S"))

        cerveja = self.rel_cerveja.get() if hasattr(self, "rel_cerveja") else "Todas"
        if cerveja and cerveja != "Todas":
            where.append("c.nome = ?")
            params.append(cerveja)

        barril_filtro = self.rel_barril.get() if hasattr(self, "rel_barril") else "Todos"
        if barril_filtro and barril_filtro != "Todos":
            try:
                barril_id_filtro = int(barril_filtro.split("•")[0].replace("#", "").strip())
                where.append("b.id = ?")
                params.append(barril_id_filtro)
            except (ValueError, IndexError):
                pass

        status = self.rel_status.get() if hasattr(self, "rel_status") else "Todos"
        if status == "Cheio":
            where.append("b.volume_atual > 0.000001 AND b.volume_atual >= b.volume_total - 0.000001")
        elif status == "Parcial":
            where.append("b.volume_atual > 0.000001 AND b.volume_atual < b.volume_total - 0.000001")
        elif status == "Vazio":
            where.append("b.volume_atual <= 0.000001")

        sql_where = " WHERE " + " AND ".join(where) if where else ""
        conn = conectar()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT v.data_hora, b.id, c.nome, v.quantidade_litros
            FROM vendas v
            JOIN barris b ON b.id = v.barril_id
            JOIN cervejas c ON c.id = b.cerveja_id
            {sql_where}
            ORDER BY v.data_hora DESC, v.id DESC
        """, params)
        rows = cur.fetchall()
        cur.execute("SELECT COALESCE(SUM(volume_atual),0), COALESCE(SUM(volume_total),0), COUNT(*) FROM barris")
        estoque_disponivel, capacidade_total, total_barris_estoque = cur.fetchone()
        conn.close()

        for item in self.tabela_relatorio.get_children():
            self.tabela_relatorio.delete(item)

        self.relatorio_linhas_exportacao = []
        consumo, por_dia = {}, {}
        barris = set()
        total_litros = 0.0
        maior_venda = 0.0

        for data_hora, barril_id, nome, litros in rows:
            total_litros += litros
            maior_venda = max(maior_venda, litros)
            barris.add(barril_id)
            consumo[nome] = consumo.get(nome, 0.0) + litros
            categoria = self.classificar_tamanho_venda(litros)
            try:
                dt = datetime.strptime(data_hora, "%Y-%m-%d %H:%M:%S")
                data_exibicao = dt.strftime("%d/%m/%Y %H:%M")
                chave_dia = dt.strftime("%Y-%m-%d")
            except ValueError:
                data_exibicao = data_hora
                chave_dia = data_hora[:10]
            por_dia[chave_dia] = por_dia.get(chave_dia, 0.0) + litros

            ml = round(litros * 1000)
            volume_txt = f"{ml} mL" if litros < 1 else f"{litros:.2f} L"
            self.tabela_relatorio.insert("", "end", values=(data_exibicao, f"#{barril_id}", nome, volume_txt, categoria))
            self.relatorio_linhas_exportacao.append([data_exibicao, barril_id, nome, f"{litros:.3f}", ml, categoria])

        total_vendas = len(rows)
        media_ml = (total_litros * 1000 / total_vendas) if total_vendas else 0
        self.lbl_rel_vendas.config(text=str(total_vendas))
        self.lbl_rel_litros.config(text=f"{total_litros:.2f} L")
        self.lbl_rel_media.config(text=f"{media_ml:.0f} mL")
        self.lbl_rel_barris.config(text=str(len(barris)))
        self.lbl_rel_qtd_linhas.config(text=f"{total_vendas} registro{'s' if total_vendas != 1 else ''}")

        ranking = sorted(consumo.items(), key=lambda x: x[1], reverse=True)
        top_nome = ranking[0][0] if ranking else "—"
        self.rel_kpi_top.config(text=top_nome)
        self.rel_kpi_maior.config(text=(f"{maior_venda*1000:.0f} mL" if maior_venda < 1 else f"{maior_venda:.2f} L") if maior_venda else "—")
        self.rel_kpi_disponivel.config(text=f"{estoque_disponivel:.2f} L")

        for child in self.frame_ranking_relatorio.winfo_children():
            child.destroy()
        if not ranking:
            tk.Label(self.frame_ranking_relatorio, text="Nenhuma venda encontrada.", bg=self.cores["superficie"], fg=self.cores["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=8)
        else:
            maior = max(v for _, v in ranking) or 1
            for pos, (nome, litros) in enumerate(ranking[:5], start=1):
                item = tk.Frame(self.frame_ranking_relatorio, bg=self.cores["superficie"])
                item.pack(fill="x", pady=(0, 9))
                topo = tk.Frame(item, bg=self.cores["superficie"])
                topo.pack(fill="x")
                tk.Label(topo, text=f"{pos}. {nome}", bg=self.cores["superficie"], fg=self.cores["texto"], font=("Segoe UI Semibold", 8)).pack(side="left")
                tk.Label(topo, text=f"{litros:.2f} L", bg=self.cores["superficie"], fg=self.cores["ambar_escuro"], font=("Segoe UI Semibold", 8)).pack(side="right")
                barra_bg = tk.Frame(item, bg=self.cores["cinza_claro"], height=5)
                barra_bg.pack(fill="x", pady=(5, 0))
                barra_bg.pack_propagate(False)
                tk.Frame(barra_bg, bg=self.cores["ambar"]).place(x=0, y=0, relwidth=max(.03, litros/maior), relheight=1)

        self.root.after(30, lambda d=por_dia.copy(): self.desenhar_grafico_relatorio(d))

        descricao = [self.rel_periodo.get()]
        if cerveja != "Todas":
            descricao.append(cerveja)
        if barril_filtro != "Todos":
            descricao.append(barril_filtro.split("•")[0].strip())
        if status != "Todos":
            descricao.append(f"barris {status.lower()}")
        self.lbl_rel_filtro_ativo.config(text=" • ".join(descricao))


if __name__ == "__main__":
    criar_banco()

    root = tk.Tk()
    app = BeerFlowApp(root)
    root.mainloop()
