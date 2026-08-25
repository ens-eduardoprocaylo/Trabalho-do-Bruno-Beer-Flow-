
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_NAME = "beerflow.db"
LIMITE_CRITICO_LITROS = 5.0


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

    conn.commit()
    conn.close()


class BeerFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BeerFlow - Controle Automatizado de Barris")
        self.root.geometry("920x620")
        self.root.minsize(820, 560)

        self.criar_interface()
        self.atualizar_tudo()

    def criar_interface(self):
        titulo = ttk.Label(
            self.root,
            text="BeerFlow",
            font=("Arial", 24, "bold")
        )
        titulo.pack(pady=(15, 2))

        subtitulo = ttk.Label(
            self.root,
            text="Controle automatizado de consumo de barris",
            font=("Arial", 11)
        )
        subtitulo.pack(pady=(0, 15))

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=15, pady=10)

        self.aba_barris = ttk.Frame(notebook)
        self.aba_adicionar_barris = ttk.Frame(notebook)
        self.aba_vendas = ttk.Frame(notebook)
        self.aba_alertas = ttk.Frame(notebook)
        self.aba_relatorio = ttk.Frame(notebook)

        notebook.add(self.aba_barris, text="Barris")
        notebook.add(self.aba_adicionar_barris, text="Adicionar barris")
        notebook.add(self.aba_vendas, text="Registrar venda")
        notebook.add(self.aba_alertas, text="Alertas")
        notebook.add(self.aba_relatorio, text="Relatório")

        self.montar_aba_barris()
        self.montar_aba_adicionar_barris()
        self.montar_aba_vendas()
        self.montar_aba_alertas()
        self.montar_aba_relatorio()

    def montar_aba_barris(self):
        resumo = ttk.LabelFrame(self.aba_barris, text="Situação dos barris")
        resumo.pack(fill="x", padx=10, pady=(10, 4))

        self.lbl_barris_cheios = ttk.Label(resumo, text="Cheios\n0", font=("Arial", 14, "bold"), justify="center")
        self.lbl_barris_parciais = ttk.Label(resumo, text="Parcialmente vendidos\n0", font=("Arial", 14, "bold"), justify="center")
        self.lbl_barris_vazios = ttk.Label(resumo, text="Vazios\n0", font=("Arial", 14, "bold"), justify="center")

        self.lbl_barris_cheios.grid(row=0, column=0, padx=30, pady=12, sticky="ew")
        self.lbl_barris_parciais.grid(row=0, column=1, padx=30, pady=12, sticky="ew")
        self.lbl_barris_vazios.grid(row=0, column=2, padx=30, pady=12, sticky="ew")
        for coluna in range(3):
            resumo.columnconfigure(coluna, weight=1)

        form = ttk.LabelFrame(self.aba_barris, text="Cadastrar novo tipo de barril")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Cerveja:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.nome_cerveja = ttk.Entry(form, width=30)
        self.nome_cerveja.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(form, text="Volume do barril (L):").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.volume_barril = ttk.Entry(form, width=15)
        self.volume_barril.grid(row=0, column=3, padx=8, pady=8)

        ttk.Button(
            form,
            text="Cadastrar barril",
            command=self.cadastrar_barril
        ).grid(row=0, column=4, padx=8, pady=8)

        tabela_frame = ttk.LabelFrame(self.aba_barris, text="Barris ativos")
        tabela_frame.pack(fill="both", expand=True, padx=10, pady=10)

        colunas = ("id", "cerveja", "total", "atual", "status")
        self.tabela_barris = ttk.Treeview(
            tabela_frame,
            columns=colunas,
            show="headings",
            height=14
        )

        titulos = {
            "id": "ID",
            "cerveja": "Cerveja",
            "total": "Volume total",
            "atual": "Volume atual",
            "status": "Status"
        }

        larguras = {"id": 60, "cerveja": 220, "total": 130, "atual": 130, "status": 180}

        for col in colunas:
            self.tabela_barris.heading(col, text=titulos[col])
            self.tabela_barris.column(col, width=larguras[col], anchor="center")

        self.tabela_barris.pack(fill="both", expand=True, padx=8, pady=8)

    def montar_aba_adicionar_barris(self):
        frame = ttk.LabelFrame(
            self.aba_adicionar_barris,
            text="Adicionar novos barris de uma cerveja já registrada"
        )
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Cerveja registrada:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.combo_cerveja_existente = ttk.Combobox(frame, state="readonly", width=35)
        self.combo_cerveja_existente.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(frame, text="Volume de cada barril (L):").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.volume_novos_barris = ttk.Entry(frame, width=18)
        self.volume_novos_barris.grid(row=1, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(frame, text="Quantidade de barris:").grid(row=2, column=0, padx=8, pady=8, sticky="w")
        self.quantidade_novos_barris = ttk.Spinbox(frame, from_=1, to=999, width=8)
        self.quantidade_novos_barris.set("1")
        self.quantidade_novos_barris.grid(row=2, column=1, padx=8, pady=8, sticky="w")

        ttk.Button(
            frame,
            text="Adicionar barris",
            command=self.adicionar_barris_existentes
        ).grid(row=3, column=0, columnspan=2, padx=8, pady=12)

        info = ttk.LabelFrame(self.aba_adicionar_barris, text="Como funciona")
        info.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Label(
            info,
            text=(
                "Use esta aba quando a cerveja já estiver cadastrada no BeerFlow.\n"
                "Informe o volume e quantos novos barris chegaram ao estoque.\n"
                "Todos serão incluídos como barris cheios e receberão novos IDs."
            ),
            font=("Arial", 12),
            justify="left"
        ).pack(anchor="w", padx=15, pady=15)

    def montar_aba_vendas(self):
        frame = ttk.LabelFrame(self.aba_vendas, text="Registrar venda")
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Barril:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.combo_barril = ttk.Combobox(frame, state="readonly", width=45)
        self.combo_barril.grid(row=0, column=1, padx=8, pady=8)

        ttk.Label(frame, text="Quantidade vendida (ml):").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.quantidade_ml = ttk.Entry(frame, width=20)
        self.quantidade_ml.grid(row=1, column=1, padx=8, pady=8, sticky="w")

        ttk.Button(
            frame,
            text="Registrar venda",
            command=self.registrar_venda
        ).grid(row=2, column=0, columnspan=2, padx=8, pady=12)

        resultado = ttk.LabelFrame(self.aba_vendas, text="Resultado da automação")
        resultado.pack(fill="both", expand=True, padx=10, pady=10)

        self.lbl_resultado = ttk.Label(
            resultado,
            text="Selecione um barril e registre uma venda.",
            font=("Arial", 14),
            justify="left"
        )
        self.lbl_resultado.pack(anchor="w", padx=15, pady=15)

    def montar_aba_alertas(self):
        frame = ttk.LabelFrame(self.aba_alertas, text="Alertas gerados automaticamente")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        colunas = ("data", "barril", "mensagem")
        self.tabela_alertas = ttk.Treeview(
            frame,
            columns=colunas,
            show="headings",
            height=18
        )

        self.tabela_alertas.heading("data", text="Data/Hora")
        self.tabela_alertas.heading("barril", text="Barril")
        self.tabela_alertas.heading("mensagem", text="Mensagem")

        self.tabela_alertas.column("data", width=160)
        self.tabela_alertas.column("barril", width=140)
        self.tabela_alertas.column("mensagem", width=500)

        self.tabela_alertas.pack(fill="both", expand=True, padx=8, pady=8)

    def montar_aba_relatorio(self):
        frame = ttk.LabelFrame(self.aba_relatorio, text="Resumo do sistema")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.txt_relatorio = tk.Text(frame, wrap="word", font=("Consolas", 11))
        self.txt_relatorio.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Button(
            self.aba_relatorio,
            text="Atualizar relatório",
            command=self.atualizar_relatorio
        ).pack(pady=(0, 10))

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

    def registrar_venda(self):
        selecao = self.combo_barril.get()
        qtd_txt = self.quantidade_ml.get().strip().replace(",", ".")

        if not selecao:
            messagebox.showwarning("Atenção", "Selecione um barril.")
            return

        try:
            quantidade_ml = float(qtd_txt)
            if quantidade_ml <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Informe uma quantidade válida em ml.")
            return

        barril_id = int(selecao.split(" - ")[0])
        quantidade_litros = quantidade_ml / 1000.0

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
            f"Quantidade vendida: {quantidade_ml:.0f} ml\n"
            f"Volume restante: {novo_volume:.2f} L"
        )

        if mensagem_alerta:
            texto += f"\n\nALERTA: {mensagem_alerta}"
            messagebox.showwarning("Alerta BeerFlow", mensagem_alerta)

        self.lbl_resultado.config(text=texto)
        self.quantidade_ml.delete(0, tk.END)
        self.atualizar_tudo()

    def atualizar_tudo(self):
        self.atualizar_barris()
        self.atualizar_resumo_barris()
        self.atualizar_combo_cervejas()
        self.atualizar_combo_barris()
        self.atualizar_alertas()
        self.atualizar_relatorio()

    def atualizar_barris(self):
        for item in self.tabela_barris.get_children():
            self.tabela_barris.delete(item)

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT b.id, c.nome, b.volume_total, b.volume_atual, b.ativo
            FROM barris b
            JOIN cervejas c ON c.id = b.cerveja_id
            ORDER BY b.id DESC
        """)

        for barril_id, nome, total, atual, ativo in cur.fetchall():
            if atual <= 0.000001:
                status = "Vazio"
            elif atual >= total - 0.000001:
                status = "Cheio"
            elif atual <= LIMITE_CRITICO_LITROS:
                status = "Parcial - nível crítico"
            else:
                status = "Parcialmente vendido"

            self.tabela_barris.insert(
                "",
                "end",
                values=(
                    barril_id,
                    nome,
                    f"{total:.2f} L",
                    f"{atual:.2f} L",
                    status
                )
            )

        conn.close()

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

        self.lbl_barris_cheios.config(text=f"Cheios\n{cheios}")
        self.lbl_barris_parciais.config(text=f"Parcialmente vendidos\n{parciais}")
        self.lbl_barris_vazios.config(text=f"Vazios\n{vazios}")

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

    def atualizar_combo_barris(self):
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

        if valores:
            self.combo_barril.current(0)
        else:
            self.combo_barril.set("")

        conn.close()

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

    def atualizar_relatorio(self):
        conn = conectar()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM barris")
        total_barris = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM barris WHERE ativo = 1")
        barris_ativos = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM barris WHERE volume_atual >= volume_total - 0.000001 AND volume_atual > 0")
        barris_cheios = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM barris WHERE volume_atual > 0.000001 AND volume_atual < volume_total - 0.000001")
        barris_parciais = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM barris WHERE volume_atual <= 0.000001")
        barris_vazios = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM vendas")
        total_vendas = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(SUM(quantidade_litros), 0) FROM vendas")
        litros_vendidos = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM alertas")
        total_alertas = cur.fetchone()[0]

        cur.execute("""
            SELECT c.nome, SUM(v.quantidade_litros)
            FROM vendas v
            JOIN barris b ON b.id = v.barril_id
            JOIN cervejas c ON c.id = b.cerveja_id
            GROUP BY c.nome
            ORDER BY SUM(v.quantidade_litros) DESC
        """)

        consumo_por_cerveja = cur.fetchall()
        conn.close()

        linhas = [
            "BEERFLOW - RELATÓRIO AUTOMÁTICO",
            "=" * 40,
            f"Total de barris cadastrados: {total_barris}",
            f"Barris ativos: {barris_ativos}",
            f"Barris cheios: {barris_cheios}",
            f"Barris parcialmente vendidos: {barris_parciais}",
            f"Barris vazios: {barris_vazios}",
            f"Total de vendas registradas: {total_vendas}",
            f"Volume total vendido: {litros_vendidos:.2f} L",
            f"Alertas gerados: {total_alertas}",
            "",
            "CONSUMO POR CERVEJA",
            "-" * 40,
        ]

        if consumo_por_cerveja:
            for nome, litros in consumo_por_cerveja:
                linhas.append(f"{nome}: {litros:.2f} L")
        else:
            linhas.append("Nenhuma venda registrada.")

        self.txt_relatorio.delete("1.0", tk.END)
        self.txt_relatorio.insert("1.0", "\n".join(linhas))


if __name__ == "__main__":
    criar_banco()

    root = tk.Tk()

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    app = BeerFlowApp(root)
    root.mainloop()
