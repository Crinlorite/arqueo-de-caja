import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
from datetime import datetime

CONFIG_FILE = "arqueo_config.json"

BILLETES = [500, 200, 100, 50, 20, 10, 5]
MONEDAS = [2, 1, 0.50, 0.20, 0.10, 0.05, 0.02, 0.01]


def get_config_path():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, CONFIG_FILE)


def load_config():
    path = get_config_path()
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"fondo_fijo": 350.0, "unidades": {}}


def save_config(data):
    path = get_config_path()
    with open(path, "w") as f:
        json.dump(data, f)


class ArqueoCaja:
    def __init__(self, root):
        self.root = root
        self.root.title("Arqueo de Caja")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Header.TLabel", font=("Segoe UI", 10, "bold"), background="#f5f5f5")
        style.configure("TLabel", font=("Segoe UI", 10), background="#f5f5f5")
        style.configure("Total.TLabel", font=("Segoe UI", 11, "bold"), background="#f5f5f5")
        style.configure("Result.TLabel", font=("Segoe UI", 12, "bold"), background="#f5f5f5", foreground="#1a5276")
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Sep.TFrame", background="#bdc3c7")

        self.config = load_config()
        config = self.config

        main = ttk.Frame(root, padding=16)
        main.pack(fill="both", expand=True)

        # Title
        ttk.Label(main, text="Arqueo de Caja", font=("Segoe UI", 16, "bold"),
                  background="#f5f5f5", foreground="#2c3e50").pack(pady=(0, 12))

        # Table frame
        table = ttk.Frame(main)
        table.pack(fill="x")

        # Column headers
        ttk.Label(table, text="Denominación", style="Header.TLabel", width=14).grid(row=0, column=0, padx=4, pady=2, sticky="w")
        ttk.Label(table, text="Uds.", style="Header.TLabel", width=8).grid(row=0, column=1, padx=4, pady=2)
        ttk.Label(table, text="Subtotal", style="Header.TLabel", width=12).grid(row=0, column=2, padx=4, pady=2, sticky="e")

        ttk.Frame(table, style="Sep.TFrame", height=1).grid(row=1, column=0, columnspan=3, sticky="ew", pady=4)

        self.entries = []
        self.subtotal_labels = []
        self.all_denominations = []
        row = 2

        # Billetes section
        ttk.Label(table, text="BILLETES", font=("Segoe UI", 9, "bold"),
                  background="#f5f5f5", foreground="#7f8c8d").grid(row=row, column=0, columnspan=3, sticky="w", pady=(4, 2))
        row += 1

        for denom in BILLETES:
            row = self._add_row(table, row, denom, is_billete=True)

        ttk.Frame(table, style="Sep.TFrame", height=1).grid(row=row, column=0, columnspan=3, sticky="ew", pady=4)
        row += 1

        # Monedas section
        ttk.Label(table, text="MONEDAS", font=("Segoe UI", 9, "bold"),
                  background="#f5f5f5", foreground="#7f8c8d").grid(row=row, column=0, columnspan=3, sticky="w", pady=(4, 2))
        row += 1

        for denom in MONEDAS:
            row = self._add_row(table, row, denom, is_billete=False)

        # Separator
        ttk.Frame(table, style="Sep.TFrame", height=2).grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1

        # Total
        ttk.Label(table, text="TOTAL ARQUEO:", style="Total.TLabel").grid(row=row, column=0, columnspan=2, sticky="w", padx=4)
        self.total_label = ttk.Label(table, text="0.00 €", style="Total.TLabel")
        self.total_label.grid(row=row, column=2, sticky="e", padx=4)
        row += 1

        # Fondo fijo section
        fondo_frame = ttk.Frame(main)
        fondo_frame.pack(fill="x", pady=(12, 0))

        ttk.Label(fondo_frame, text="Fondo fijo de caja:", style="Header.TLabel").pack(side="left")

        self.fondo_var = tk.StringVar(value=str(config["fondo_fijo"]))
        self.fondo_var.trace_add("write", lambda *_: self._update_totals())
        fondo_entry = ttk.Entry(fondo_frame, textvariable=self.fondo_var, width=10,
                                font=("Segoe UI", 10), justify="right")
        fondo_entry.pack(side="left", padx=8)
        ttk.Label(fondo_frame, text="€").pack(side="left")

        # Result
        result_frame = ttk.Frame(main)
        result_frame.pack(fill="x", pady=(8, 0))

        ttk.Frame(result_frame, style="Sep.TFrame", height=1).pack(fill="x", pady=4)

        row_frame = ttk.Frame(result_frame)
        row_frame.pack(fill="x")
        ttk.Label(row_frame, text="RESULTADO:", style="Result.TLabel").pack(side="left")
        self.result_label = ttk.Label(row_frame, text="0.00 €", style="Result.TLabel")
        self.result_label.pack(side="right")

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(16, 0))

        ttk.Button(btn_frame, text="Limpiar campos", command=self._clear_all).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Exportar resumen", command=self._export_summary).pack(side="left")

        # Restore saved units
        saved_units = config.get("unidades", {})
        for i, denom in enumerate(self.all_denominations):
            key = str(denom)
            if key in saved_units and saved_units[key]:
                self.entries[i].set(saved_units[key])

        self._update_totals()

        # Save on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _add_row(self, parent, row, denom, is_billete):
        self.all_denominations.append(denom)

        if denom >= 1:
            label_text = f"{int(denom)} €" if denom == int(denom) else f"{denom:.2f} €"
        else:
            label_text = f"{denom:.2f} €"

        if is_billete:
            label_text = f"💶  {label_text}"
        else:
            label_text = f"🪙  {label_text}"

        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=4, pady=1, sticky="w")

        var = tk.StringVar(value="")
        var.trace_add("write", lambda *_: self._update_totals())
        entry = ttk.Entry(parent, textvariable=var, width=8, font=("Segoe UI", 10), justify="center")
        entry.grid(row=row, column=1, padx=4, pady=1)

        sub_label = ttk.Label(parent, text="0.00 €", width=12, anchor="e")
        sub_label.grid(row=row, column=2, padx=4, pady=1, sticky="e")

        self.entries.append(var)
        self.subtotal_labels.append(sub_label)
        return row + 1

    def _get_units(self, var):
        try:
            val = int(var.get())
            return val if val >= 0 else 0
        except ValueError:
            return 0

    def _get_fondo(self):
        try:
            return float(self.fondo_var.get().replace(",", "."))
        except ValueError:
            return 0.0

    def _update_totals(self):
        total = 0.0
        for i, (denom, var) in enumerate(zip(self.all_denominations, self.entries)):
            units = self._get_units(var)
            subtotal = denom * units
            total += subtotal
            self.subtotal_labels[i].configure(text=f"{subtotal:.2f} €")

        self.total_label.configure(text=f"{total:.2f} €")

        fondo = self._get_fondo()
        resultado = total - fondo
        sign = "+" if resultado >= 0 else ""
        color = "#27ae60" if resultado >= 0 else "#c0392b"
        if abs(resultado) < 0.005:
            color = "#2c3e50"

        self.result_label.configure(text=f"{sign}{resultado:.2f} €", foreground=color)

    def _save_state(self):
        unidades = {}
        for i, denom in enumerate(self.all_denominations):
            val = self.entries[i].get()
            if val:
                unidades[str(denom)] = val
        save_config({
            "fondo_fijo": self._get_fondo(),
            "unidades": unidades,
        })

    def _on_close(self):
        self._save_state()
        self.root.destroy()

    def _clear_all(self):
        for var in self.entries:
            var.set("")

    def _get_base_dir(self):
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _export_summary(self):
        now = datetime.now()
        fecha = now.strftime("%d/%m/%Y")
        hora = now.strftime("%H:%M")
        filename_ts = now.strftime("%Y-%m-%d_%H-%M")

        lines = []
        lines.append("=" * 40)
        lines.append("         ARQUEO DE CAJA")
        lines.append("=" * 40)
        lines.append(f"  Fecha:  {fecha}")
        lines.append(f"  Hora:   {hora}")
        lines.append("-" * 40)
        lines.append("")

        total = 0.0
        total_billetes = 0.0
        total_monedas = 0.0

        lines.append("  BILLETES")
        lines.append("  " + "-" * 36)
        for i, denom in enumerate(self.all_denominations):
            if denom not in BILLETES:
                continue
            units = self._get_units(self.entries[i])
            if units > 0:
                sub = denom * units
                total_billetes += sub
                label = f"{int(denom)}€" if denom == int(denom) else f"{denom:.2f}€"
                lines.append(f"  {label:>8} x {units:<6} = {sub:>10.2f}€")
        lines.append(f"  {'Subtotal billetes:':>28} {total_billetes:>8.2f}€")
        lines.append("")

        lines.append("  MONEDAS")
        lines.append("  " + "-" * 36)
        for i, denom in enumerate(self.all_denominations):
            if denom not in MONEDAS:
                continue
            units = self._get_units(self.entries[i])
            if units > 0:
                sub = denom * units
                total_monedas += sub
                label = f"{int(denom)}€" if denom >= 1 and denom == int(denom) else f"{denom:.2f}€"
                lines.append(f"  {label:>8} x {units:<6} = {sub:>10.2f}€")
        lines.append(f"  {'Subtotal monedas:':>28} {total_monedas:>8.2f}€")
        lines.append("")

        total = total_billetes + total_monedas
        fondo = self._get_fondo()
        resultado = total - fondo
        sign = "+" if resultado >= 0 else ""

        lines.append("=" * 40)
        lines.append(f"  TOTAL ARQUEO:    {total:>18.2f}€")
        lines.append(f"  FONDO FIJO:      {fondo:>18.2f}€")
        lines.append("-" * 40)
        lines.append(f"  RESULTADO:       {sign}{resultado:>17.2f}€")
        lines.append("=" * 40)

        text = "\n".join(lines)

        # Save to file
        export_dir = os.path.join(self._get_base_dir(), "arqueos")
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, f"arqueo_{filename_ts}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        messagebox.showinfo("Exportado", f"Resumen guardado en:\n{filepath}")


def main():
    root = tk.Tk()
    root.configure(bg="#f5f5f5")
    ArqueoCaja(root)
    root.mainloop()


if __name__ == "__main__":
    main()
