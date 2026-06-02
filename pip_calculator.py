import threading
import urllib.request
import xml.etree.ElementTree as ET

import tkinter as tk
from tkinter import font as tkfont, ttk

# ── colori ──────────────────────────────────────────────────────────────────
BG        = "#0d1117"
CARD      = "#161b22"
BORDER    = "#30363d"
ACCENT    = "#58a6ff"
ACCENT2   = "#3fb950"
RED       = "#f85149"
YELLOW    = "#d29922"
TEXT      = "#e6edf3"
TEXT_DIM  = "#8b949e"
INPUT_BG  = "#0d1117"

# ── Strumenti con valore pip per lotto standard (100.000 unità) in EUR ──────
INSTRUMENTS = {
    "Forex Major": {
        "EUR/USD":  8.93,
        "GBP/USD":  8.93,
        "USD/JPY":  6.25,
        "USD/CHF":  9.92,
        "AUD/USD":  8.93,
        "NZD/USD":  8.93,
        "USD/CAD":  6.52,
    },
    "Forex Minor": {
        "EUR/GBP":  11.96,
        "EUR/JPY":   6.25,
        "EUR/CHF":   9.92,
        "EUR/AUD":   5.80,
        "EUR/CAD":   6.52,
        "EUR/NZD":   4.95,
        "GBP/JPY":   7.46,
        "GBP/CHF":  11.84,
        "GBP/AUD":   6.92,
        "GBP/CAD":   7.78,
        "AUD/JPY":   4.06,
        "AUD/CHF":   6.44,
        "AUD/CAD":   4.24,
        "AUD/NZD":   5.35,
        "CAD/JPY":   5.68,
        "CHF/JPY":   7.78,
        "NZD/JPY":   3.75,
        "NZD/CAD":   3.91,
        "NZD/CHF":   5.95,
    },
    "Forex Exotic": {
        "USD/TRY":   0.28,
        "USD/MXN":   0.46,
        "USD/ZAR":   0.49,
        "USD/SEK":   0.84,
        "USD/NOK":   0.83,
        "USD/HKD":   1.14,
        "USD/SGD":   6.65,
        "USD/PLN":   2.24,
        "EUR/TRY":   0.31,
        "EUR/SEK":   0.94,
        "EUR/NOK":   0.93,
        "EUR/PLN":   2.51,
        "GBP/TRY":   0.37,
    },
    "Indici": {
        "DAX 40":           1.00,
        "FTSE 100":         1.19,
        "CAC 40":           1.00,
        "Euro Stoxx 50":    1.00,
        "IBEX 35":          1.00,
        "SP500 (US500)":    8.93,
        "NAS100":           8.93,
        "DJ30 (US30)":      8.93,
        "Nikkei 225":       0.06,
        "Hang Seng":        1.14,
        "ASX 200":          5.80,
    },
    "Commodities": {
        "Gold (XAU/USD)":   0.89,
        "Silver (XAG/USD)": 4.46,
        "Petrolio WTI":     8.93,
        "Petrolio Brent":   8.93,
        "Gas Naturale":     8.93,
        "Rame":             3.57,
        "Platino":          0.89,
        "Palladio":         0.89,
    },
    "Crypto": {
        "BTC/USD":  0.089,
        "ETH/USD":  0.450,
        "XRP/USD":  8.930,
        "LTC/USD":  8.930,
        "BCH/USD":  8.930,
    },
}

CATEGORIES = list(INSTRUMENTS.keys())

# ── Fonte dati ufficiale e gratuita: tassi di riferimento BCE (base EUR) ─────
# https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/
# Aggiornati ogni giorno lavorativo (~16:00 CET). Nessuna chiave API richiesta.
FOREX_CATEGORIES = {"Forex Major", "Forex Minor", "Forex Exotic"}
CONTRACT_SIZE = 100_000          # 1 lotto standard = 100.000 unità
ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_NS = {
    "g": "http://www.gesmes.org/xml/2002-08-01",
    "e": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
}


def fetch_ecb_rates(timeout=15):
    """Scarica i tassi di riferimento ufficiali della BCE (base EUR).

    Ritorna (data, {valuta: tasso}) dove il tasso è 'quante unità della
    valuta per 1 EUR'. Solleva un'eccezione in caso di errore di rete.
    """
    raw = urllib.request.urlopen(ECB_URL, timeout=timeout).read()
    day = ET.fromstring(raw).find(".//e:Cube/e:Cube[@time]", ECB_NS)
    rates = {"EUR": 1.0}
    for cube in day.findall("e:Cube", ECB_NS):
        rates[cube.get("currency")] = float(cube.get("rate"))
    return day.get("time"), rates


def pip_value_eur(pair, rates):
    """Valore di 1 pip in EUR per 1 lotto standard, calcolato dai tassi BCE.

    valore_pip_EUR = (dimensione_pip × lotto) / tasso(valuta_quotata)
    Ritorna None se la coppia non è calcolabile dai dati disponibili.
    """
    if "/" not in pair:
        return None
    quote = pair.split("/")[1].strip()
    if quote not in rates:
        return None
    pip_size = 0.01 if quote == "JPY" else 0.0001
    return pip_size * CONTRACT_SIZE / rates[quote]


class PipCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PIP Calculator")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.fn      = tkfont.Font(family="Segoe UI", size=10)
        self.fn_bold = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.fn_big  = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.fn_sm   = tkfont.Font(family="Segoe UI", size=9)
        self.fn_h    = tkfont.Font(family="Segoe UI", size=11, weight="bold")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                         fieldbackground=INPUT_BG,
                         background=BORDER,
                         foreground=ACCENT,
                         selectbackground=BORDER,
                         selectforeground=ACCENT,
                         arrowcolor=ACCENT,
                         bordercolor=BORDER,
                         lightcolor=BORDER,
                         darkcolor=BORDER)
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", INPUT_BG)],
                  foreground=[("readonly", ACCENT)],
                  selectbackground=[("readonly", BORDER)],
                  selectforeground=[("readonly", ACCENT)])

        self._build_ui()
        self._calc()
        self._refresh_rates()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=BG)
        title_frame.pack(fill="x", padx=20, pady=(18, 4))
        tk.Label(title_frame, text="📊  PIP CALCULATOR",
                 font=tkfont.Font(family="Segoe UI", size=15, weight="bold"),
                 bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(title_frame, text="  💶 Conto: EUR",
                 font=tkfont.Font(family="Segoe UI", size=10),
                 bg=BG, fg=ACCENT2).pack(side="left", padx=(8, 0))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(0, 12))

        wrapper = tk.Frame(self, bg=BG)
        wrapper.pack(padx=20, pady=(0, 20))

        # ── SELETTORE STRUMENTO ──────────────────────────────────────────────
        sel_outer, sel_card = self._card(wrapper, "🔍  SELEZIONA STRUMENTO")
        sel_outer.pack(fill="x", pady=(0, 12))

        row_cat = tk.Frame(sel_card, bg=CARD)
        row_cat.pack(fill="x", padx=14, pady=4)
        tk.Label(row_cat, text="📂  Categoria", font=self.fn, bg=CARD,
                 fg=TEXT, width=22, anchor="w").pack(side="left")
        self.cat_var = tk.StringVar(value=CATEGORIES[0])
        self.cat_cb  = ttk.Combobox(row_cat, textvariable=self.cat_var,
                                    values=CATEGORIES, state="readonly",
                                    style="Dark.TCombobox", width=22,
                                    font=self.fn_bold)
        self.cat_cb.pack(side="left", padx=(0, 6))
        self.cat_cb.bind("<<ComboboxSelected>>", self._on_category_change)

        row_str = tk.Frame(sel_card, bg=CARD)
        row_str.pack(fill="x", padx=14, pady=4)
        tk.Label(row_str, text="📌  Strumento", font=self.fn, bg=CARD,
                 fg=TEXT, width=22, anchor="w").pack(side="left")
        first_instr = list(INSTRUMENTS[CATEGORIES[0]].keys())
        self.instr_var = tk.StringVar(value=first_instr[0])
        self.instr_cb  = ttk.Combobox(row_str, textvariable=self.instr_var,
                                      values=first_instr, state="readonly",
                                      style="Dark.TCombobox", width=22,
                                      font=self.fn_bold)
        self.instr_cb.pack(side="left", padx=(0, 6))
        self.instr_cb.bind("<<ComboboxSelected>>", self._on_instrument_change)

        nota_row = tk.Frame(sel_card, bg=CARD)
        nota_row.pack(fill="x", padx=14, pady=(0, 2))
        tk.Label(nota_row,
                 text="ℹ️  Valore pip per 1 lotto standard (100.000 unità) in €",
                 font=self.fn_sm, bg=CARD, fg=TEXT_DIM, anchor="w").pack(side="left")

        status_row = tk.Frame(sel_card, bg=CARD)
        status_row.pack(fill="x", padx=14, pady=(0, 8))
        # il pulsante viene impacchettato per primo a destra, così riserva
        # sempre il suo spazio e la scritta di stato non lo spinge fuori
        self.refresh_btn = tk.Button(status_row, text="🔄  Aggiorna",
                                     font=self.fn_sm, bg=BORDER, fg=ACCENT,
                                     activebackground=ACCENT, activeforeground=BG,
                                     relief="flat", bd=0, padx=12, pady=3,
                                     cursor="hand2", command=self._refresh_rates)
        self.refresh_btn.pack(side="right")
        self.refresh_btn.bind("<Enter>", lambda e: self._btn_hover(True))
        self.refresh_btn.bind("<Leave>", lambda e: self._btn_hover(False))
        self.status_lbl = tk.Label(status_row, text="⏳  Carico i tassi BCE…",
                                   font=self.fn_sm, bg=CARD, fg=TEXT_DIM, anchor="w")
        self.status_lbl.pack(side="left", fill="x", expand=True)

        # ── INPUT ────────────────────────────────────────────────────────────
        in_outer, in_card = self._card(wrapper, "✏️  PARAMETRI DI INPUT")
        in_outer.pack(fill="x", pady=(0, 12))

        self.vars = {}
        default_pip = INSTRUMENTS[CATEGORIES[0]][first_instr[0]]
        inputs = [
            ("saldo",   "💰  Saldo (€)",         "780",            "€"),
            ("rischio", "⚠️  Rischio (%)",        "1",              "%"),
            ("pip",     "📏  Valore Pip (€)",     f"{default_pip}", "€"),
            ("sl",      "🔴  Stop Loss (pips)",   "5",              "pips"),
            ("tp",      "🟢  Take Profit (pips)", "20",             "pips"),
        ]
        for key, label, default, unit in inputs:
            row = tk.Frame(in_card, bg=CARD)
            row.pack(fill="x", padx=14, pady=4)
            tk.Label(row, text=label, font=self.fn, bg=CARD,
                     fg=TEXT, width=22, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            self.vars[key] = var
            tk.Entry(row, textvariable=var,
                     font=self.fn_bold, bg=INPUT_BG, fg=ACCENT,
                     insertbackground=ACCENT, relief="flat", bd=0, width=12,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT, justify="right").pack(side="left", padx=(0, 6))
            var.trace_add("write", lambda *_: self._calc())
            tk.Label(row, text=unit, font=self.fn_sm, bg=CARD,
                     fg=TEXT_DIM).pack(side="left")

        # ── OUTPUT ───────────────────────────────────────────────────────────
        out_outer, out_card = self._card(wrapper, "📈  RISULTATI CALCOLATI")
        out_outer.pack(fill="x")

        self.result_labels = {}
        for key, label, color in [
            ("rischio_eur", "💸  Rischio in €",   YELLOW),
            ("volume",      "📦  Volume (lotti)",  ACCENT),
            ("rr",          "⚖️  Rapporto R/R",    TEXT),
            ("sl_eur",      "🔴  SL in €",         RED),
            ("tp_eur",      "🟢  TP in €",         ACCENT2),
        ]:
            row = tk.Frame(out_card, bg=CARD)
            row.pack(fill="x", padx=14, pady=5)
            tk.Label(row, text=label, font=self.fn, bg=CARD,
                     fg=TEXT_DIM, width=22, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="—", font=self.fn_big, bg=CARD,
                           fg=color, anchor="e", width=14)
            lbl.pack(side="right")
            self.result_labels[key] = lbl

        # ── footer ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(self,
                 text="Volume = Rischio€ ÷ (SL pips × Valore Pip)  ·  Forex: tassi ufficiali BCE",
                 font=self.fn_sm, bg=BG, fg=TEXT_DIM).pack(pady=(4, 12))

    def _card(self, parent, title):
        outer = tk.Frame(parent, bg=BORDER, bd=1)
        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(inner, text=title, font=self.fn_h,
                 bg=CARD, fg=TEXT).pack(anchor="w", padx=14, pady=(10, 2))
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(0, 4))
        return outer, inner

    # ── Tassi ufficiali BCE ──────────────────────────────────────────────────
    def _btn_hover(self, on):
        if str(self.refresh_btn["state"]) == "normal":
            self.refresh_btn.config(bg=ACCENT if on else BORDER,
                                    fg=BG if on else ACCENT)

    def _refresh_rates(self):
        self.status_lbl.config(text="⏳  Carico i tassi BCE…", fg=TEXT_DIM)
        self.refresh_btn.config(state="disabled")
        threading.Thread(target=self._load_rates_async, daemon=True).start()

    def _load_rates_async(self):
        try:
            date, rates = fetch_ecb_rates()
            self.after(0, self._apply_rates, date, rates)
        except Exception:
            self.after(0, self._rates_failed)

    def _apply_rates(self, date, rates):
        updated = 0
        for cat in FOREX_CATEGORIES:
            for pair in INSTRUMENTS.get(cat, {}):
                value = pip_value_eur(pair, rates)
                if value is not None:
                    INSTRUMENTS[cat][pair] = round(value, 4)
                    updated += 1
        self.status_lbl.config(
            text=f"✅  Tassi BCE {date} · {updated} forex",
            fg=ACCENT2)
        self.refresh_btn.config(state="normal", fg=ACCENT)
        if self.cat_var.get() in FOREX_CATEGORIES:
            self._on_instrument_change()

    def _rates_failed(self):
        self.status_lbl.config(
            text="⚠️  Offline · valori stimati",
            fg=YELLOW)
        self.refresh_btn.config(state="normal", fg=ACCENT)

    def _on_category_change(self, event=None):
        cat = self.cat_var.get()
        instruments = list(INSTRUMENTS[cat].keys())
        self.instr_cb["values"] = instruments
        self.instr_var.set(instruments[0])
        self._on_instrument_change()

    def _on_instrument_change(self, event=None):
        cat   = self.cat_var.get()
        instr = self.instr_var.get()
        pip_val = INSTRUMENTS.get(cat, {}).get(instr, "")
        if pip_val != "":
            self.vars["pip"].set(str(pip_val))
        self._calc()

    def _calc(self):
        try:
            saldo   = float(self.vars["saldo"].get().replace(",", "."))
            rischio = float(self.vars["rischio"].get().replace(",", ".")) / 100
            pip_val = float(self.vars["pip"].get().replace(",", "."))
            sl_pip  = float(self.vars["sl"].get().replace(",", "."))
            tp_pip  = float(self.vars["tp"].get().replace(",", "."))

            rischio_eur = saldo * rischio
            volume      = rischio_eur / (sl_pip * pip_val) if sl_pip and pip_val else 0
            sl_eur      = volume * sl_pip * pip_val
            tp_eur      = volume * tp_pip * pip_val
            rr          = tp_pip / sl_pip if sl_pip else 0

            self.result_labels["rischio_eur"].config(text=f"€ {rischio_eur:.2f}")
            self.result_labels["volume"].config(text=f"{volume:.4f}")
            self.result_labels["rr"].config(text=f"1 : {rr:.2f}")
            self.result_labels["sl_eur"].config(text=f"€ {sl_eur:.2f}")
            self.result_labels["tp_eur"].config(text=f"€ {tp_eur:.2f}")

            color = ACCENT2 if rr >= 2 else (YELLOW if rr >= 1 else RED)
            self.result_labels["rr"].config(fg=color)

        except (ValueError, ZeroDivisionError):
            for lbl in self.result_labels.values():
                lbl.config(text="—")


if __name__ == "__main__":
    app = PipCalculator()
    app.update_idletasks()
    w, h = app.winfo_reqwidth(), app.winfo_reqheight()
    sw, sh = app.winfo_screenwidth(), app.winfo_screenheight()
    app.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    app.mainloop()
