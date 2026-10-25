"""
Λογαριασμοί σπιτιού – εφαρμογή Android (Kivy).
Ίδια λογική με το πρόγραμμα υπολογιστή: ρεύμα, φυσικό αέριο, internet, κινητή.
"""
import threading
import time
import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import NoTransition, Screen
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

import engine
import mobile_format
import store

AUTO_UPDATE_HOURS = 12
Window.clearcolor = (0.953, 0.961, 0.957, 1)

KV = """
#:import dp kivy.metrics.dp

<WrapLabel>:
    size_hint_y: None
    markup: True
    color: 0.11, 0.14, 0.2, 1
    halign: 'left'
    valign: 'top'
    text_size: self.width - dp(28), None
    height: self.texture_size[1] + dp(16)
    padding: dp(14), dp(8)

<RowCard>:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.x + dp(8), self.y + dp(3)
            size: self.width - dp(16), self.height - dp(6)
            radius: [dp(10)]

<SectionTitle@Label>:
    size_hint_y: None
    height: dp(40)
    bold: True
    font_size: '16sp'
    color: 0.29, 0.33, 0.41, 1
    halign: 'left'
    valign: 'middle'
    text_size: self.width - dp(28), None

<NavButton@ToggleButton>:
    group: 'nav'
    allow_no_selection: False
    font_size: '12sp'
    background_normal: ''
    background_down: ''
    background_color: (0.95, 0.71, 0.14, 1) if self.state == 'down' else (0.11, 0.14, 0.2, 1)
    color: (0.11, 0.14, 0.2, 1) if self.state == 'down' else (1, 1, 1, 1)

<FormLabel@Label>:
    color: 0.11, 0.14, 0.2, 1
    halign: 'left'
    valign: 'middle'
    text_size: self.width, None
    size_hint_y: None
    height: dp(48)

<Root>:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: None
        height: dp(60)
        padding: dp(12), dp(8)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: 0.11, 0.14, 0.2, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: 'Λογαριασμοί σπιτιού'
            bold: True
            font_size: '18sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size
        Button:
            id: update_btn
            text: 'ΕΝΗΜΕΡΩΣΗ ΟΛΩΝ'
            bold: True
            size_hint_x: None
            width: dp(170)
            background_normal: ''
            background_color: 0.95, 0.71, 0.14, 1
            color: 0.11, 0.14, 0.2, 1
            on_release: app.update_all()
    Label:
        id: msg
        size_hint_y: None
        height: dp(30)
        font_size: '12sp'
        color: 0.29, 0.33, 0.41, 1
        text_size: self.width - dp(20), None
        halign: 'left'
        shorten: True
    ScreenManager:
        id: sm
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        NavButton:
            text: 'Καλύτερο'
            state: 'down'
            on_release: app.show('best')
        NavButton:
            text: 'Ρεύμα'
            on_release: app.show('electricity')
        NavButton:
            text: 'Αέριο'
            on_release: app.show('gas')
        NavButton:
            text: 'Internet'
            on_release: app.show('internet')
        NavButton:
            text: 'Κινητή'
            on_release: app.show('mobile')
        NavButton:
            text: 'Ρυθμίσεις'
            on_release: app.show('settings')
"""


class WrapLabel(Label):
    pass


class RowCard(ButtonBehavior, WrapLabel):
    url = StringProperty("")

    def on_release(self):
        if self.url:
            webbrowser.open(self.url)


class Root(BoxLayout):
    pass


Builder.load_string(KV)


def scroll_column():
    from kivy.uix.scrollview import ScrollView
    sv = ScrollView(do_scroll_x=False)
    col = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2), padding=(0, dp(6)))
    col.bind(minimum_height=col.setter("height"))
    sv.add_widget(col)
    return sv, col


class LogariasmoiApp(App):
    title = "Λογαριασμοί σπιτιού"

    def build(self):
        store.set_dir(self.user_data_dir)
        self.d = store.load()
        self.busy = False
        self._job = None
        self.root_w = Root()
        sm = self.root_w.ids.sm
        sm.transition = NoTransition()
        self.columns = {}
        for name in ["best"] + engine.SERVICES:
            scr = Screen(name=name)
            sv, col = scroll_column()
            scr.add_widget(sv)
            sm.add_widget(scr)
            self.columns[name] = col
        set_scr = Screen(name="settings")
        sv, col = scroll_column()
        set_scr.add_widget(sv)
        sm.add_widget(set_scr)
        self._build_settings(col)
        self.refresh()
        last = max([s.get("updated") or 0 for s in self.d["services"].values()])
        if time.time() - last > AUTO_UPDATE_HOURS * 3600:
            Clock.schedule_once(lambda dt: self.update_all(), 1)
        return self.root_w

    # ------------------------------------------------------------ οθόνες
    def show(self, name):
        self.root_w.ids.sm.current = name

    def refresh(self):
        col = self.columns["best"]
        col.clear_widgets()
        col.add_widget(WrapLabel(text=mobile_format.report_markup(self.d)))
        for s in engine.SERVICES:
            col = self.columns[s]
            col.clear_widgets()
            col.add_widget(WrapLabel(text=f"[size=19sp][b]{engine.LABELS[s]}[/b][/size]\n"
                                          f"[size=12sp]Πάτα ένα πρόγραμμα για τη σελίδα του.[/size]"))
            for title, rows in mobile_format.service_sections(self.d, s):
                col.add_widget(Label(text=title, size_hint_y=None, height=dp(40), bold=True,
                                     color=(0.29, 0.33, 0.41, 1), halign="left", valign="middle",
                                     text_size=(Window.width - dp(28), None)))
                if not rows:
                    col.add_widget(WrapLabel(text="Κανένα πρόγραμμα με τα κριτήριά σου."))
                for i, (markup, url) in enumerate(rows):
                    col.add_widget(RowCard(text=markup, url=url))
        self.root_w.ids.msg.text = store.status_line(self.d)

    # ------------------------------------------------------------ ρυθμίσεις
    def _build_settings(self, col):
        p = self.d["profile"]
        self.w = {}
        col.padding = (dp(14), dp(8))
        col.spacing = dp(4)

        def title(t):
            col.add_widget(Label(text=t, size_hint_y=None, height=dp(44), bold=True, font_size="16sp",
                                 color=(0.11, 0.14, 0.2, 1), halign="left", valign="bottom",
                                 text_size=(Window.width - dp(28), None)))

        def row(label, widget):
            b = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            b.add_widget(Label(text=label, color=(0.11, 0.14, 0.2, 1), halign="left", valign="middle",
                               text_size=(Window.width * 0.6, None), size_hint_x=0.65))
            widget.size_hint_x = 0.35
            b.add_widget(widget)
            col.add_widget(b)

        def check(key, label, value):
            cb = CheckBox(active=bool(value), color=(0.11, 0.14, 0.2, 1))
            cb.bind(active=lambda *a: self._changed())
            self.w[key] = cb
            row(label, cb)

        def number(key, label, value):
            ti = TextInput(text=f"{value:g}", input_filter="float", multiline=False, font_size="16sp")
            ti.bind(text=lambda *a: self._changed())
            self.w[key] = ti
            row(label, ti)

        def choice(key, label, value, values):
            sp = Spinner(text=value, values=values)
            sp.bind(text=lambda *a: self._changed())
            self.w[key] = sp
            row(label, sp)

        title("Τι θέλεις να συγκρίνω")
        for s in engine.SERVICES:
            check("need_" + s, engine.LABELS[s], s in p["need"])
        title("Ενέργεια")
        number("kwh_month", "Ρεύμα: kWh τον μήνα", p["kwh_month"])
        number("gas_kwh_year", "Αέριο: kWh τον χρόνο", p["gas_kwh_year"])
        choice("heating", "Θέρμανση", p["heating"], ["Αυτόνομη", "Κεντρική"])
        for t in engine.DEFAULTS["el_types"]:
            check("el_" + t, t, t in p["el_types"])
        check("keep_discounts", "Πληρώνω πάντα στην ώρα μου", p["keep_discounts"])
        title("Τηλεπικοινωνίες")
        number("min_mbps", "Internet: τουλάχιστον Mbps", p["min_mbps"])
        check("fwa", "Δέχομαι 4G/5G internet", "4G/5G" in p["net_techs"])
        check("sat", "Δέχομαι δορυφορικό", "Δορυφορικό" in p["net_techs"])
        number("min_gb", "Κινητή: τουλάχιστον GB", p["min_gb"])
        number("mobile_lines", "Γραμμές κινητού", p["mobile_lines"])
        check("unlimited_voice", "Απεριόριστη ομιλία", p["unlimited_voice"])
        choice("mobile_type", "Είδος κινητής", p["mobile_type"], ["Όλα", "Συμβόλαιο", "Καρτοκινητό"])
        title("Εξαίρεση εταιρειών (με κόμμα)")
        ti = TextInput(text=", ".join(p["exclude_providers"]), multiline=False, size_hint_y=None, height=dp(44))
        ti.bind(text=lambda *a: self._changed())
        self.w["exclude"] = ti
        col.add_widget(ti)

    def _changed(self):
        if self._job:
            self._job.cancel()
        self._job = Clock.schedule_once(lambda dt: self._recalc(), 0.6)

    def _recalc(self):
        w, p = self.w, self.d["profile"]

        def f(k, default):
            try:
                return float(w[k].text.replace(",", "."))
            except ValueError:
                return default
        p["need"] = [s for s in engine.SERVICES if w["need_" + s].active]
        p["kwh_month"] = f("kwh_month", 300)
        p["gas_kwh_year"] = f("gas_kwh_year", 6000)
        p["min_mbps"] = f("min_mbps", 0)
        p["min_gb"] = f("min_gb", 0)
        p["mobile_lines"] = max(1, int(f("mobile_lines", 1)))
        p["heating"] = w["heating"].text
        p["el_types"] = [t for t in engine.DEFAULTS["el_types"] if w["el_" + t].active]
        p["keep_discounts"] = w["keep_discounts"].active
        p["net_techs"] = ["Fiber/VDSL"] + (["4G/5G"] if w["fwa"].active else []) + \
                         (["Δορυφορικό"] if w["sat"].active else [])
        p["unlimited_voice"] = w["unlimited_voice"].active
        p["mobile_type"] = w["mobile_type"].text
        p["exclude_providers"] = [x.strip() for x in w["exclude"].text.split(",") if x.strip()]
        try:
            store.save(self.d)
        except OSError:
            pass
        self.refresh()

    # ------------------------------------------------------------ ενημέρωση
    def update_all(self):
        if self.busy:
            return
        self.busy = True
        btn = self.root_w.ids.update_btn
        btn.disabled = True
        btn.text = "ΕΝΗΜΕΡΩΣΗ…"
        self.root_w.ids.msg.text = "Λήψη τρεχουσών τιμών από όλες τις εταιρείες…"

        def work():
            try:
                errors = store.update_all(self.d)
            except Exception as e:  # noqa: BLE001
                errors = {s: str(e) for s in engine.SERVICES}
            Clock.schedule_once(lambda dt: self._done(errors))

        threading.Thread(target=work, daemon=True).start()

    def _done(self, errors):
        self.busy = False
        btn = self.root_w.ids.update_btn
        btn.disabled = False
        btn.text = "ΕΝΗΜΕΡΩΣΗ ΟΛΩΝ"
        self.refresh()
        failed = {s: e for s, e in errors.items() if e}
        if not failed:
            self.root_w.ids.msg.text = "Ενημερώθηκαν όλες οι τιμές " + time.strftime("%d/%m/%Y %H:%M")
            return
        lines = []
        for s, e in failed.items():
            lines.append(f"[b]{engine.LABELS[s]}[/b]\n" + "\n".join("• " + x for x in e.split("\n")))
        content = WrapLabel(text="\n\n".join(lines) + "\n\nΤα αποτελέσματα βγαίνουν με τις τελευταίες "
                                                      "αποθηκευμένες τιμές.")
        from kivy.uix.scrollview import ScrollView
        sv = ScrollView()
        content.color = (1, 1, 1, 1)
        sv.add_widget(content)
        Popup(title="Δεν ενημερώθηκαν όλες οι τιμές", content=sv, size_hint=(0.92, 0.6)).open()


if __name__ == "__main__":
    LogariasmoiApp().run()
