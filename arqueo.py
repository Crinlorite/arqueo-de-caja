import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import subprocess
import re
import time
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
        return {"fondo_fijo": 350.0, "unidades": {}, "trabajador": "", "impresora": ""}


def save_config(data):
    path = get_config_path()
    with open(path, "w") as f:
        json.dump(data, f)


class ArqueoCaja:
    # ── ESC/POS — Epson TM-T20 ────────────────────────────────────────────────
    _ESC_INIT     = b'\x1b\x40'
    _ESC_CP858    = b'\x1b\x74\x13'   # CP858: español + €
    _ESC_CENTER   = b'\x1b\x61\x01'
    _ESC_BOLD_ON  = b'\x1b\x45\x01'
    _ESC_BOLD_OFF = b'\x1b\x45\x00'
    _CUT_FULL     = b'\n\n\n\n\n\x1d\x56\x00'  # 4 líneas de avance + corte
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

        # Trabajador
        trab_frame = ttk.Frame(main)
        trab_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(trab_frame, text="Trabajador:", style="Header.TLabel").pack(side="left")
        self.trabajador_var = tk.StringVar(value=config.get("trabajador", ""))
        trab_entry = ttk.Entry(trab_frame, textvariable=self.trabajador_var, width=20,
                               font=("Segoe UI", 10))
        trab_entry.pack(side="left", padx=8)

        # Fondo fijo section
        fondo_frame = ttk.Frame(main)
        fondo_frame.pack(fill="x", pady=(6, 0))

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
        ttk.Button(btn_frame, text="Exportar resumen", command=self._export_summary).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="🖨 Imprimir", command=self._print_summary).pack(side="left", padx=(0, 8))

        btn_frame2 = ttk.Frame(main)
        btn_frame2.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_frame2, text="📂 Cargar sesión anterior", command=self._show_load_dialog).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame2, text="⚙ Configuración", command=self._show_config).pack(side="left")

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
            "trabajador": self.trabajador_var.get(),
            "impresora": self.config.get("impresora", ""),
        })

    def _on_close(self):
        self._save_state()
        self._export_summary(silent=True)
        self.root.destroy()

    def _clear_all(self):
        for var in self.entries:
            var.set("")

    def _get_base_dir(self):
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _build_ticket(self):
        now = datetime.now()
        fecha = now.strftime("%d/%m/%Y")
        hora = now.strftime("%H:%M")

        lines = []
        lines.append("==================")
        lines.append("  ARQUEO DE CAJA")
        lines.append("==================")
        lines.append(f"Fecha: {fecha} {hora}")
        trabajador = self.trabajador_var.get().strip()
        if trabajador:
            lines.append(f"Trab: {trabajador}")
        lines.append("------------------")

        total_billetes = 0.0
        total_monedas = 0.0

        lines.append("BILLETES")
        for i, denom in enumerate(self.all_denominations):
            if denom not in BILLETES:
                continue
            units = self._get_units(self.entries[i])
            if units > 0:
                sub = denom * units
                total_billetes += sub
                label = f"{int(denom)}€" if denom == int(denom) else f"{denom:.2f}€"
                lines.append(f" {label} x{units} = {sub:.2f}€")
        lines.append(f"Sub: {total_billetes:.2f}€")

        lines.append("MONEDAS")
        for i, denom in enumerate(self.all_denominations):
            if denom not in MONEDAS:
                continue
            units = self._get_units(self.entries[i])
            if units > 0:
                sub = denom * units
                total_monedas += sub
                label = f"{int(denom)}€" if denom >= 1 and denom == int(denom) else f"{denom:.2f}€"
                lines.append(f" {label} x{units} = {sub:.2f}€")
        lines.append(f"Sub: {total_monedas:.2f}€")

        total = total_billetes + total_monedas
        fondo = self._get_fondo()
        resultado = total - fondo
        sign = "+" if resultado >= 0 else ""

        lines.append("==================")
        lines.append(f"TOTAL: {total:.2f}€")
        lines.append(f"FONDO: {fondo:.2f}€")
        lines.append("------------------")
        lines.append(f"RESULTADO: {sign}{resultado:.2f}€")
        lines.append("==================")

        return "\n".join(lines), now

    def _export_summary(self, silent=False):
        text, now = self._build_ticket()
        filename_ts = now.strftime("%Y-%m-%d_%H-%M")

        export_dir = os.path.join(self._get_base_dir(), "arqueos")
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, f"arqueo_{filename_ts}.txt")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        if not silent:
            messagebox.showinfo("Exportado", f"Resumen guardado en:\n{filepath}")

        return filepath

    def _get_printers(self):
        """List available printers via PowerShell."""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-Printer | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            printers = [p.strip() for p in result.stdout.strip().splitlines() if p.strip()]
            return printers
        except Exception:
            return []

    def _raw_print(self, data: bytes, printer: str):
        """Envía bytes RAW directamente a la impresora (sin GDI ni márgenes)."""
        import win32print
        h = win32print.OpenPrinter(printer)
        try:
            win32print.StartDocPrinter(h, 1, ("Arqueo", None, "RAW"))
            try:
                win32print.StartPagePrinter(h)
                win32print.WritePrinter(h, data)
                win32print.EndPagePrinter(h)
            finally:
                win32print.EndDocPrinter(h)
        finally:
            win32print.ClosePrinter(h)

    def _print_summary(self):
        printer = self.config.get("impresora", "")
        if not printer:
            messagebox.showwarning("Sin impresora",
                                   "No hay impresora configurada.\nVe a Configuración para seleccionar una.")
            return
        self._export_summary(silent=True)
        text, _ = self._build_ticket()
        try:
            payload = (
                self._ESC_INIT
                + self._ESC_CP858
                + self._ESC_CENTER
                + text.encode("cp858", errors="replace")
                + self._CUT_FULL
            )
            self._raw_print(payload, printer)
        except Exception as e:
            messagebox.showerror("Error al imprimir", str(e))

    def _show_config(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Configuración")
        dialog.resizable(False, False)
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()

        ttk.Label(dialog, text="Impresora de la app:", style="Header.TLabel").pack(
            padx=16, pady=(12, 6), anchor="w")

        frame = ttk.Frame(dialog)
        frame.pack(padx=16, fill="both", expand=True)

        listbox = tk.Listbox(frame, font=("Segoe UI", 10), width=45, height=8)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        printers = self._get_printers()
        current = self.config.get("impresora", "")

        if not printers:
            listbox.insert("end", "(No se encontraron impresoras)")
        else:
            for i, name in enumerate(printers):
                prefix = "✔ " if name == current else "   "
                listbox.insert("end", f"{prefix}{name}")
                if name == current:
                    listbox.selection_set(i)

        # Current printer label
        status_var = tk.StringVar(value=f"Actual: {current}" if current else "Actual: (ninguna)")
        ttk.Label(dialog, textvariable=status_var, font=("Segoe UI", 9),
                  background="#f5f5f5", foreground="#7f8c8d").pack(padx=16, anchor="w")

        def on_save():
            sel = listbox.curselection()
            if not sel or not printers:
                return
            selected = printers[sel[0]]
            self.config["impresora"] = selected
            self._save_state()
            dialog.destroy()
            messagebox.showinfo("Configuración", f"Impresora guardada:\n{selected}")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=(8, 12))
        ttk.Button(btn_frame, text="Guardar", command=on_save).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side="left")

    def _scan_arqueos(self):
        """Scan arqueos/ folder and return list of (display_label, filepath)."""
        export_dir = os.path.join(self._get_base_dir(), "arqueos")
        if not os.path.isdir(export_dir):
            return []

        results = []
        for fname in sorted(os.listdir(export_dir), reverse=True):
            if not fname.startswith("arqueo_") or not fname.endswith(".txt"):
                continue
            fpath = os.path.join(export_dir, fname)
            # Parse header to build a friendly label
            trabajador = ""
            fecha = ""
            hora = ""
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("Fecha:"):
                            # "Fecha: 15/03/2026 12:00" or "Fecha: 15/03/2026  Hora: 12:00"
                            parts = line.split()
                            if len(parts) >= 2:
                                fecha = parts[1]
                            if "Hora:" in parts:
                                idx = parts.index("Hora:")
                                if idx + 1 < len(parts):
                                    hora = parts[idx + 1]
                            elif len(parts) >= 3:
                                hora = parts[2]
                        elif line.startswith("Trab:") or line.startswith("Trabajador:"):
                            trabajador = line.split(":", 1)[1].strip()
                        elif line.startswith("-") and fecha:
                            break
            except Exception:
                continue

            label = f"{fecha}  {hora}"
            if trabajador:
                label += f"  —  {trabajador}"
            results.append((label, fpath))

        return results

    def _show_load_dialog(self):
        all_arqueos = self._scan_arqueos()
        if not all_arqueos:
            messagebox.showinfo("Cargar sesión", "No hay arqueos guardados.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Cargar sesión anterior")
        dialog.resizable(False, False)
        dialog.configure(bg="#f5f5f5")
        dialog.grab_set()

        # Filter by date
        filter_frame = ttk.Frame(dialog)
        filter_frame.pack(padx=16, pady=(12, 6), fill="x")
        ttk.Label(filter_frame, text="Filtrar por fecha:", style="Header.TLabel").pack(side="left")
        filter_var = tk.StringVar(value="")
        filter_entry = ttk.Entry(filter_frame, textvariable=filter_var, width=12,
                                 font=("Segoe UI", 10))
        filter_entry.pack(side="left", padx=8)
        ttk.Label(filter_frame, text="(día, año, trabajador...)").pack(side="left")

        frame = ttk.Frame(dialog)
        frame.pack(padx=16, fill="both", expand=True)

        listbox = tk.Listbox(frame, font=("Segoe UI", 10), width=40, height=12)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Keep filtered list in sync
        filtered = []

        def refresh_list(*_):
            nonlocal filtered
            listbox.delete(0, "end")
            filtered.clear()
            query = filter_var.get().strip()
            for label, fpath in all_arqueos:
                # Filter: each word must match somewhere in the label
                if query:
                    words = query.lower().split()
                    label_lower = label.lower()
                    if not all(w in label_lower for w in words):
                        continue
                filtered.append((label, fpath))
            for label, _ in filtered:
                listbox.insert("end", label)
            if filtered:
                listbox.selection_set(0)

        filter_var.trace_add("write", refresh_list)
        refresh_list()

        def on_load():
            sel = listbox.curselection()
            if not sel or sel[0] >= len(filtered):
                return
            _, fpath = filtered[sel[0]]
            dialog.destroy()
            self._load_from_file(fpath)

        ttk.Button(dialog, text="Cargar", command=on_load).pack(pady=(8, 12))
        listbox.bind("<Double-1>", lambda e: on_load())

    def _load_from_file(self, filepath):
        """Parse a ticket txt and restore values into the UI."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
            return

        # Clear all fields first
        self._clear_all()

        # Parse trabajador
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("Trab:") or stripped.startswith("Trabajador:"):
                self.trabajador_var.set(stripped.split(":", 1)[1].strip())
            elif stripped.startswith("FONDO:"):
                # "FONDO:               350.00€"
                val = stripped.replace("FONDO:", "").replace("€", "").strip()
                try:
                    self.fondo_var.set(str(float(val)))
                except ValueError:
                    pass

        # Parse denomination lines: " {label:>6} x{units:<4}= {sub:>8.2f}€"
        denom_pattern = re.compile(r"^\s*([\d.]+)€\s*x(\d+)\s*=")
        for line in content.splitlines():
            m = denom_pattern.match(line.strip())
            if m:
                denom_str = m.group(1)
                units_str = m.group(2)
                try:
                    denom_val = float(denom_str)
                except ValueError:
                    continue
                # Find matching denomination index
                for i, d in enumerate(self.all_denominations):
                    if abs(d - denom_val) < 0.001:
                        self.entries[i].set(units_str)
                        break

        self._update_totals()


def main():
    root = tk.Tk()
    root.configure(bg="#f5f5f5")
    ArqueoCaja(root)
    root.mainloop()


if __name__ == "__main__":
    main()
