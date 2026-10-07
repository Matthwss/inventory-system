"""
Sistema de Estoque Simples
--------------------------
- Cadastrar um novo item no catálogo
- Adicionar manualmente quantidade de um item que já existe

Requisitos: apenas Python 3.8+ (tkinter e sqlite3 já vêm com o Python).
Como rodar: python estoque.py
Os dados ficam salvos no arquivo "estoque.db", na mesma pasta do script.
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "estoque.db")


# ---------------------------------------------------------------- Banco de dados
def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS itens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT NOT NULL UNIQUE COLLATE NOCASE,
            codigo     TEXT,
            quantidade INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    return conn


def cadastrar_item(conn, nome, codigo, quantidade):
    conn.execute(
        "INSERT INTO itens (nome, codigo, quantidade) VALUES (?, ?, ?)",
        (nome, codigo, quantidade),
    )
    conn.commit()


def adicionar_quantidade(conn, item_id, quantidade):
    conn.execute(
        "UPDATE itens SET quantidade = quantidade + ? WHERE id = ?",
        (quantidade, item_id),
    )
    conn.commit()


def listar_itens(conn, filtro=""):
    termo = f"%{filtro}%"
    return conn.execute(
        """
        SELECT id, nome, COALESCE(codigo, ''), quantidade
        FROM itens
        WHERE nome LIKE ? OR codigo LIKE ?
        ORDER BY nome
        """,
        (termo, termo),
    ).fetchall()


# ---------------------------------------------------------------- Interface
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Estoque")
        self.geometry("760x520")
        self.minsize(680, 460)
        self.conn = conectar()

        self.var_nome = tk.StringVar()
        self.var_codigo = tk.StringVar()
        self.var_qtd_inicial = tk.StringVar(value="0")
        self.var_qtd_add = tk.StringVar(value="1")
        self.var_busca = tk.StringVar()
        self.var_busca.trace_add("write", lambda *_: self.atualizar_lista())

        self.montar_tela()
        self.atualizar_lista()

    def montar_tela(self):
        topo = ttk.Frame(self, padding=10)
        topo.pack(fill="x")

        # --- Novo item
        novo = ttk.LabelFrame(topo, text="Novo item no catálogo", padding=10)
        novo.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ttk.Label(novo, text="Nome:").grid(row=0, column=0, sticky="w")
        ttk.Entry(novo, textvariable=self.var_nome, width=28).grid(row=0, column=1, pady=2)
        ttk.Label(novo, text="Código (opcional):").grid(row=1, column=0, sticky="w")
        ttk.Entry(novo, textvariable=self.var_codigo, width=28).grid(row=1, column=1, pady=2)
        ttk.Label(novo, text="Quantidade inicial:").grid(row=2, column=0, sticky="w")
        ttk.Entry(novo, textvariable=self.var_qtd_inicial, width=10).grid(
            row=2, column=1, sticky="w", pady=2
        )
        ttk.Button(novo, text="Cadastrar item", command=self.on_cadastrar).grid(
            row=3, column=0, columnspan=2, pady=(8, 0), sticky="ew"
        )

        # --- Adicionar quantidade
        add = ttk.LabelFrame(topo, text="Adicionar ao estoque", padding=10)
        add.pack(side="left", fill="both", expand=True, padx=(5, 0))

        ttk.Label(add, text="1) Selecione um item na lista abaixo").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(add, text="2) Quantidade a adicionar:").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(add, textvariable=self.var_qtd_add, width=10).grid(row=1, column=1, sticky="w")
        ttk.Button(add, text="Adicionar quantidade", command=self.on_adicionar).grid(
            row=2, column=0, columnspan=2, pady=(8, 0), sticky="ew"
        )

        # --- Lista
        meio = ttk.Frame(self, padding=(10, 0, 10, 0))
        meio.pack(fill="x")
        ttk.Label(meio, text="Buscar:").pack(side="left")
        ttk.Entry(meio, textvariable=self.var_busca).pack(side="left", fill="x", expand=True, padx=5)

        baixo = ttk.Frame(self, padding=10)
        baixo.pack(fill="both", expand=True)

        colunas = ("nome", "codigo", "quantidade")
        self.tabela = ttk.Treeview(baixo, columns=colunas, show="headings", selectmode="browse")
        self.tabela.heading("nome", text="Item")
        self.tabela.heading("codigo", text="Código")
        self.tabela.heading("quantidade", text="Em estoque")
        self.tabela.column("nome", width=330)
        self.tabela.column("codigo", width=140)
        self.tabela.column("quantidade", width=100, anchor="center")

        barra = ttk.Scrollbar(baixo, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    # ---------------------------------------------------------- Ações
    def atualizar_lista(self, selecionar_id=None):
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)
        for item_id, nome, codigo, qtd in listar_itens(self.conn, self.var_busca.get().strip()):
            self.tabela.insert("", "end", iid=str(item_id), values=(nome, codigo, qtd))
        if selecionar_id and self.tabela.exists(str(selecionar_id)):
            self.tabela.selection_set(str(selecionar_id))
            self.tabela.see(str(selecionar_id))

    @staticmethod
    def ler_inteiro(texto, campo, minimo):
        try:
            valor = int(texto.strip())
        except ValueError:
            messagebox.showwarning("Valor inválido", f"{campo} deve ser um número inteiro.")
            return None
        if valor < minimo:
            messagebox.showwarning("Valor inválido", f"{campo} deve ser no mínimo {minimo}.")
            return None
        return valor

    def on_cadastrar(self):
        nome = self.var_nome.get().strip()
        codigo = self.var_codigo.get().strip() or None
        if not nome:
            messagebox.showwarning("Faltou o nome", "Digite o nome do item.")
            return
        qtd = self.ler_inteiro(self.var_qtd_inicial.get(), "Quantidade inicial", 0)
        if qtd is None:
            return
        try:
            cadastrar_item(self.conn, nome, codigo, qtd)
        except sqlite3.IntegrityError:
            messagebox.showwarning("Item já existe", f'Já existe um item chamado "{nome}".')
            return
        self.var_nome.set("")
        self.var_codigo.set("")
        self.var_qtd_inicial.set("0")
        self.atualizar_lista()

    def on_adicionar(self):
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showinfo("Selecione um item", "Clique em um item da lista primeiro.")
            return
        qtd = self.ler_inteiro(self.var_qtd_add.get(), "Quantidade a adicionar", 1)
        if qtd is None:
            return
        item_id = int(selecao[0])
        adicionar_quantidade(self.conn, item_id, qtd)
        self.var_qtd_add.set("1")
        self.atualizar_lista(selecionar_id=item_id)


if __name__ == "__main__":
    App().mainloop()
