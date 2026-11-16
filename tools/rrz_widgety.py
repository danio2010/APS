"""Interaktywne widgety do lekcji „Równania różniczkowe” (RRZ dla laików).

Zasada: Python liczy, JavaScript rysuje. Funkcje z tego pliku dostają wyniki obliczeń
(np. z metody Eulera w notatniku) i wyświetlają je jako widget HTML + JavaScript.
Dzięki temu suwaki działają zarówno w Jupyterze, jak i w notatniku wyeksportowanym do HTML
(jupyter nbconvert --to html) – bez działającego Pythona.

Plik musi leżeć w tym samym folderze co notatnik.
"""
import json
import uuid

import numpy as np
from IPython.display import HTML, display

_JS = r"""/* RRZ – interaktywne widgety do notatnika „Równania różniczkowe dla laików”.
   Zasada: Python liczy (dane przychodzą jako JSON), JavaScript tylko rysuje.
   Wyjątki (liczone w przeglądarce, bo muszą działać płynnie): Lotka–Volterra, trzy ciała. */
(function () {
  var WERSJA = "2026.11.5";
  if (window.RRZ && window.RRZ.wersja === WERSJA) return;
  var RRZ = (window.RRZ = { wersja: WERSJA, W: {} });

  var K = {
    granat: "#1d3557", morski: "#2a9d8f", koral: "#e76f51", piasek: "#f4a261",
    zloty: "#e9c46a", fiolet: "#6d597a", tekst: "#22303f", slaby: "#5b6b7c",
    siatka: "#e3e8ee", os: "#8a99a8", tlo: "#ffffff", pole: "#9aa8b6"
  };
  RRZ.K = K;
  var FONT = "'Source Sans 3', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif";

  /* ---------- styl (wstrzykiwany raz) ---------- */
  var CSS = [
    ".rrz-w{font-family:" + FONT + ";background:#fff;color:#22303f;border:1px solid #d8e0e8;border-radius:12px;",
    "padding:14px 16px 12px;margin:10px 0;max-width:980px;box-shadow:0 2px 10px rgba(29,53,87,.08);box-sizing:border-box}",
    ".rrz-w *{box-sizing:border-box}",
    ".rrz-w-tytul{font-family:'Lexend'," + FONT + ";font-weight:600;font-size:17px;color:#1d3557;margin:0 0 2px}",
    ".rrz-w-opis{font-size:14.5px;color:#5b6b7c;margin:0 0 8px;line-height:1.4}",
    ".rrz-w-plotno{width:100%;position:relative}",
    ".rrz-w-plotno canvas{display:block;width:100%;touch-action:manipulation}",
    ".rrz-w-rzad{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;margin:8px 0 2px}",
    ".rrz-w-suwak{display:flex;align-items:center;gap:8px;font-size:15px;flex:1 1 auto}",
    ".rrz-w-suwak label{white-space:nowrap;flex:0 0 auto}",
    ".rrz-w-suwak b{color:#1d3557;font-variant-numeric:tabular-nums;display:inline-block;min-width:4.2em}",
    ".rrz-w-suwak input[type=range]{flex:1 1 140px;accent-color:#2a9d8f;min-width:140px;height:22px;margin:0;padding:0}",
    ".rrz-w button.rrz-w-btn{font-family:inherit;font-size:14.5px;border:1.5px solid #2a9d8f;background:#fff;color:#1d3557;",
    "border-radius:999px;padding:4px 13px;cursor:pointer;line-height:1.3}",
    ".rrz-w button.rrz-w-btn:hover{background:#eaf6f3}",
    ".rrz-w button.rrz-w-btn.rrz-on{background:#2a9d8f;color:#fff}",
    ".rrz-w button.rrz-w-btn.rrz-akcent{border-color:#e76f51;background:#e76f51;color:#fff}",
    ".rrz-w button.rrz-w-btn.rrz-akcent:hover{background:#d65f42}",
    ".rrz-w button.rrz-w-btn:disabled{opacity:.45;cursor:default}",
    ".rrz-w-info{font-size:15px;line-height:1.45;margin-top:6px;padding:7px 11px;background:#f4f7fa;border-radius:8px;min-height:1.5em}",
    ".rrz-w-info b{color:#1d3557}",
    ".rrz-w-info .rrz-dobrze{color:#1f7a6f;font-weight:700}.rrz-w-info .rrz-zle{color:#c4522f;font-weight:700}",
    ".rrz-w-kolumny{display:flex;flex-wrap:wrap;gap:12px}.rrz-w-kolumny>div{flex:1 1 300px;min-width:0}",
    ".rrz-w-tabela{border-collapse:collapse;font-size:14.5px;margin:2px 0}",
    ".rrz-w-tabela td,.rrz-w-tabela th{padding:2px 10px;border-bottom:1px solid #e3e8ee;text-align:right}",
    ".rrz-w-tabela th{color:#1d3557;text-align:left}",
    ".rrz-w-tabela td:first-child{text-align:left}"
  ].join("");
  function wstawStyl() {
    if (document.getElementById("rrz-w-css-" + WERSJA)) return;
    var s = document.createElement("style");
    s.id = "rrz-w-css-" + WERSJA;
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  /* ---------- drobne narzędzia DOM ---------- */
  function el(tag, cls, rodzic, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    if (rodzic) rodzic.appendChild(e);
    return e;
  }
  RRZ.el = el;
  function liczba(x, n) {
    return Number(x).toFixed(n == null ? 1 : n).replace(".", ",").replace("-", "−");
  }
  RRZ.liczba = liczba;

  function szkielet(root, tytul, opis) {
    wstawStyl();
    root.classList.add("rrz-w");
    root.innerHTML = "";
    if (tytul) el("div", "rrz-w-tytul", root, tytul);
    if (opis) el("div", "rrz-w-opis", root, opis);
    return root;
  }

  function suwak(rodzic, o) {
    // o: {etykieta, min, max, krok, wartosc, format(v)->str, zmiana(v)}
    var w = el("div", "rrz-w-suwak", rodzic);
    var lab = el("label", null, w);
    var inp = el("input", null, w);
    inp.type = "range"; inp.min = o.min; inp.max = o.max; inp.step = o.krok || 1; inp.value = o.wartosc;
    function odswiez() {
      var v = Number(inp.value);
      lab.innerHTML = o.etykieta + " <b>" + (o.format ? o.format(v) : v) + "</b>";
    }
    inp.addEventListener("input", function () { odswiez(); o.zmiana && o.zmiana(Number(inp.value)); });
    odswiez();
    return {
      input: inp,
      ustaw: function (v) { inp.value = v; odswiez(); },
      wartosc: function () { return Number(inp.value); },
      odswiez: odswiez
    };
  }
  function przycisk(rodzic, tekst, klik, cls) {
    var b = el("button", "rrz-w-btn" + (cls ? " " + cls : ""), rodzic, tekst);
    b.type = "button";
    b.addEventListener("click", klik);
    return b;
  }
  function przelacznik(rodzic, tekst, start, zmiana) {
    var stan = !!start;
    var b = przycisk(rodzic, "", function () { stan = !stan; rysuj(); zmiana(stan); });
    function rysuj() { b.innerHTML = (stan ? "✓ " : "") + tekst; b.classList.toggle("rrz-on", stan); }
    rysuj();
    return { przycisk: b, stan: function () { return stan; }, ustaw: function (s) { stan = s; rysuj(); } };
  }

  /* ---------- wykres na płótnie ---------- */
  function Wykres(rodzic, o) {
    // o: {proporcja: wys/szer, maksWys, margines:{l,r,t,b}}
    var self = this;
    this.o = o || {};
    this.m = Object.assign({ l: 62, r: 18, t: 30, b: 50 }, this.o.margines || {});
    this.box = el("div", "rrz-w-plotno", rodzic);
    this.cv = el("canvas", null, this.box);
    this.ctx = this.cv.getContext("2d");
    this.W = 0; this.H = 0;
    this.rysuj = function () {};
    var poprzW = -1;
    function rozmiar() {
      var w = Math.round(self.box.clientWidth);
      if (!w || w === poprzW) return;
      poprzW = w;
      var h = Math.round(Math.min(w * (self.o.proporcja || 0.56), self.o.maksWys || 560));
      if (self.o.minWys) h = Math.max(h, self.o.minWys);
      var dpr = window.devicePixelRatio || 1;
      self.cv.width = Math.round(w * dpr); self.cv.height = Math.round(h * dpr);
      self.cv.style.height = h + "px";
      self.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      self.W = w; self.H = h;
      self.rysuj();
    }
    this.rozmiar = rozmiar;
    if (window.ResizeObserver) new ResizeObserver(rozmiar).observe(this.box);
    window.addEventListener("resize", rozmiar);
    setTimeout(rozmiar, 0); setTimeout(rozmiar, 300);
  }
  RRZ.Wykres = Wykres;
  var P = Wykres.prototype;
  P.zakres = function (x0, x1, y0, y1, logX) {
    this.x0 = x0; this.x1 = x1; this.y0 = y0; this.y1 = y1; this.logX = !!logX;
  };
  P.X = function (x) {
    var m = this.m, a = this.x0, b = this.x1, u = x;
    if (this.logX) { a = Math.log10(a); b = Math.log10(b); u = Math.log10(x); }
    return m.l + (u - a) / (b - a) * (this.W - m.l - m.r);
  };
  P.Y = function (y) {
    var m = this.m;
    return this.H - m.b - (y - this.y0) / (this.y1 - this.y0) * (this.H - m.t - m.b);
  };
  P.odwrotnieX = function (px) {
    var m = this.m;
    return this.x0 + (px - m.l) / (this.W - m.l - m.r) * (this.x1 - this.x0);
  };
  P.odwrotnieY = function (py) {
    var m = this.m;
    return this.y0 + (this.H - m.b - py) / (this.H - m.t - m.b) * (this.y1 - this.y0);
  };
  P.pxNaJedn = function () {
    var m = this.m;
    return [(this.W - m.l - m.r) / (this.x1 - this.x0), (this.H - m.t - m.b) / (this.y1 - this.y0)];
  };
  function ladneKroki(a, b, n) {
    var zakres = b - a, surowy = zakres / (n || 6);
    var p = Math.pow(10, Math.floor(Math.log10(surowy))), r = surowy / p;
    var krok = (r < 1.5 ? 1 : r < 3 ? 2 : r < 7 ? 5 : 10) * p;
    var t = [], x = Math.ceil(a / krok - 1e-9) * krok;
    for (; x <= b + 1e-9 * zakres; x += krok) t.push(Math.abs(x) < krok * 1e-9 ? 0 : x);
    return { t: t, krok: krok };
  }
  P.rama = function (o) {
    // o: {xEtykieta, yEtykieta, tytul, xTicki, yTicki, format}
    o = o || {};
    var c = this.ctx, m = this.m, self = this;
    c.save();
    c.clearRect(0, 0, this.W, this.H);
    c.fillStyle = K.tlo; c.fillRect(0, 0, this.W, this.H);
    c.font = "13px " + FONT; c.fillStyle = K.slaby; c.strokeStyle = K.siatka; c.lineWidth = 1;
    var xt, yt;
    if (this.logX) {
      xt = o.xTicki || [];
    } else {
      xt = o.xTicki || ladneKroki(this.x0, this.x1, Math.max(3, Math.round((this.W - m.l - m.r) / 90))).t;
    }
    yt = o.yTicki || ladneKroki(this.y0, this.y1, Math.max(3, Math.round((this.H - m.t - m.b) / 55))).t;
    var fx = o.formatX || function (v) { return String(+v.toFixed(6)).replace(".", ","); };
    var fy = o.formatY || function (v) { return String(+v.toFixed(6)).replace(".", ","); };
    c.textAlign = "center"; c.textBaseline = "top";
    xt.forEach(function (v) {
      var x = Math.round(self.X(v)) + 0.5;
      c.beginPath(); c.moveTo(x, m.t); c.lineTo(x, self.H - m.b); c.stroke();
      c.fillText(fx(v), x, self.H - m.b + 6);
    });
    c.textAlign = "right"; c.textBaseline = "middle";
    yt.forEach(function (v) {
      var y = Math.round(self.Y(v)) + 0.5;
      c.beginPath(); c.moveTo(m.l, y); c.lineTo(self.W - m.r, y); c.stroke();
      c.fillText(fy(v), m.l - 7, y);
    });
    c.strokeStyle = K.os; c.lineWidth = 1.2;
    c.beginPath(); c.moveTo(m.l, m.t); c.lineTo(m.l, this.H - m.b); c.lineTo(this.W - m.r, this.H - m.b); c.stroke();
    c.fillStyle = K.tekst; c.font = "14px " + FONT;
    if (o.xEtykieta) { c.textAlign = "center"; c.textBaseline = "bottom"; c.fillText(o.xEtykieta, (m.l + this.W - m.r) / 2, this.H - 4); }
    if (o.yEtykieta) {
      c.save(); c.translate(14, (m.t + this.H - m.b) / 2); c.rotate(-Math.PI / 2);
      c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(o.yEtykieta, 0, 0); c.restore();
    }
    if (o.tytul) {
      c.font = "600 15px " + FONT; c.fillStyle = K.granat; c.textAlign = "left"; c.textBaseline = "top";
      c.fillText(o.tytul, m.l, 6);
    }
    c.restore();
  };
  P.klip = function () {
    var c = this.ctx, m = this.m;
    c.save(); c.beginPath(); c.rect(m.l, m.t - 2, this.W - m.l - m.r + 2, this.H - m.t - m.b + 2); c.clip();
  };
  P.odklip = function () { this.ctx.restore(); };
  P.linia = function (xs, ys, s) {
    s = s || {};
    var c = this.ctx; c.save();
    c.strokeStyle = s.kolor || K.granat; c.lineWidth = s.grubosc || 2.6; c.globalAlpha = s.alfa == null ? 1 : s.alfa;
    c.lineJoin = "round"; c.lineCap = "round";
    if (s.kreski) c.setLineDash(s.kreski);
    c.beginPath();
    var start = true;
    for (var i = 0; i < xs.length; i++) {
      if (xs[i] == null || ys[i] == null || !isFinite(ys[i])) { start = true; continue; }
      var x = this.X(xs[i]), y = this.Y(ys[i]);
      if (start) { c.moveTo(x, y); start = false; } else c.lineTo(x, y);
    }
    c.stroke(); c.restore();
  };
  P.punkty = function (xs, ys, s) {
    s = s || {};
    var c = this.ctx; c.save();
    c.fillStyle = s.kolor || K.koral; c.strokeStyle = s.obrys || "#fff"; c.lineWidth = s.obrysGr || 1.5;
    c.globalAlpha = s.alfa == null ? 1 : s.alfa;
    for (var i = 0; i < xs.length; i++) {
      c.beginPath(); c.arc(this.X(xs[i]), this.Y(ys[i]), s.r || 5, 0, 2 * Math.PI); c.fill(); if (s.obrys !== null) c.stroke();
    }
    c.restore();
  };
  P.pozioma = function (y, s) { this.linia([this.x0, this.x1], [y, y], Object.assign({ grubosc: 1.6, kreski: [6, 5] }, s || {})); };
  P.pionowa = function (x, s) { this.linia([x, x], [this.y0, this.y1], Object.assign({ grubosc: 1.6, kreski: [6, 5] }, s || {})); };
  // strzałka wyśrodkowana w (x,y), kierunek (dx,dy) w jednostkach danych, długość L w pikselach
  P.strzalka = function (x, y, dx, dy, s) {
    s = s || {};
    var c = this.ctx, k = this.pxNaJedn();
    var ux = dx * k[0], uy = -dy * k[1], n = Math.hypot(ux, uy);
    if (!n) return;
    var L = s.dl || 18; ux = ux / n * L / 2; uy = uy / n * L / 2;
    var X = this.X(x), Y = this.Y(y), x2 = X + ux, y2 = Y + uy;
    c.save(); c.strokeStyle = c.fillStyle = s.kolor || K.pole; c.globalAlpha = s.alfa == null ? 1 : s.alfa;
    c.lineWidth = s.grubosc || 1.5; c.lineCap = "round";
    c.beginPath(); c.moveTo(X - ux, Y - uy); c.lineTo(x2, y2); c.stroke();
    var g = s.grot || Math.max(4, L * 0.28), a = Math.atan2(uy, ux);
    c.beginPath(); c.moveTo(x2, y2);
    c.lineTo(x2 - g * Math.cos(a - 0.45), y2 - g * Math.sin(a - 0.45));
    c.lineTo(x2 - g * Math.cos(a + 0.45), y2 - g * Math.sin(a + 0.45));
    c.closePath(); c.fill(); c.restore();
  };
  P.tekst = function (x, y, t, s) {
    s = s || {};
    var c = this.ctx; c.save();
    c.font = (s.waga || "") + " " + (s.rozmiar || 13) + "px " + FONT;
    c.textAlign = s.wyrown || "left"; c.textBaseline = s.linia || "middle";
    var X = s.px ? x : this.X(x), Y = s.px ? y : this.Y(y);
    X += s.dx || 0; Y += s.dy || 0;
    if (s.tlo) {
      var w = c.measureText(t).width, h = (s.rozmiar || 13) + 6;
      var x0 = c.textAlign === "center" ? X - w / 2 : c.textAlign === "right" ? X - w : X;
      c.fillStyle = s.tlo; c.globalAlpha = 0.88; c.fillRect(x0 - 4, Y - h / 2, w + 8, h); c.globalAlpha = 1;
    }
    c.fillStyle = s.kolor || K.tekst; c.fillText(t, X, Y); c.restore();
  };
  P.legenda = function (pozycje, gdzie) {
    var c = this.ctx, m = this.m, self = this;
    c.save(); c.font = "13px " + FONT;
    var szer = 0; pozycje.forEach(function (p) { szer = Math.max(szer, c.measureText(p.tekst).width); });
    var w = szer + 44, h = pozycje.length * 20 + 8;
    var x = gdzie === "lewo" ? m.l + 8 : this.W - m.r - w - 4, y = gdzie === "dol" ? this.H - m.b - h - 6 : m.t + 4;
    c.fillStyle = "rgba(255,255,255,.88)"; c.fillRect(x, y, w, h);
    pozycje.forEach(function (p, i) {
      var yy = y + 14 + i * 20;
      c.strokeStyle = c.fillStyle = p.kolor; c.lineWidth = p.grubosc || 2.6;
      if (p.typ === "punkt") { c.beginPath(); c.arc(x + 16, yy, 5, 0, 7); c.fill(); }
      else { c.setLineDash(p.kreski || []); c.beginPath(); c.moveTo(x + 4, yy); c.lineTo(x + 28, yy); c.stroke(); c.setLineDash([]); }
      c.fillStyle = K.tekst; c.textBaseline = "middle"; c.fillText(p.tekst, x + 36, yy);
    });
    c.restore();
  };

  /* =====================================================================
     1. Krzywe z suwakami (dowolna liczba parametrów; krzywe policzone w Pythonie)
     ===================================================================== */
  RRZ.W.krzywe = function (root, d) {
    szkielet(root, d.tytul, d.opis);
    var wyk = new Wykres(root, { proporcja: 0.55, maksWys: 470 });
    var kontrolki = el("div", "rrz-w-rzad", root);
    var info = d.info ? el("div", "rrz-w-info", root) : null;
    var idx = d.parametry.map(function (p) { return p.start || 0; });
    d.parametry.forEach(function (p, i) {
      suwak(kontrolki, {
        etykieta: p.nazwa, min: 0, max: p.etykiety.length - 1, krok: 1, wartosc: idx[i],
        format: function (v) { return p.etykiety[v]; },
        zmiana: function (v) { idx[i] = v; wyk.rysuj(); }
      });
    });
    function plaski() { var k = 0; for (var i = 0; i < idx.length; i++) k = k * d.parametry[i].etykiety.length + idx[i]; return k; }
    function wstaw(sz) { return sz.replace(/\{(\d)\}/g, function (_, i) { return d.parametry[+i].etykiety[idx[+i]]; }); }
    wyk.rysuj = function () {
      if (!wyk.W) return;
      var k = plaski();
      wyk.zakres(d.xlim[0], d.xlim[1], d.ylim[0], d.ylim[1]);
      wyk.rama({ xEtykieta: d.xlabel, yEtykieta: d.ylabel, tytul: d.tytuly ? d.tytuly[k] : "" });
      wyk.klip();
      var leg = [];
      (d.poziome || []).forEach(function (h) {
        wyk.pozioma(h.y, { kolor: h.kolor, kreski: h.kreski || [6, 5] });
        if (h.etykieta) leg.push({ tekst: h.etykieta, kolor: h.kolor, kreski: h.kreski || [6, 5], grubosc: 1.6 });
      });
      if (d.pozioma_param) {
        var hp = d.pozioma_param, y = d.parametry[hp.param].wartosci[idx[hp.param]];
        wyk.pozioma(y, { kolor: hp.kolor, kreski: [3, 4] });
        leg.push({ tekst: wstaw(hp.etykieta), kolor: hp.kolor, kreski: [3, 4], grubosc: 1.6 });
      }
      wyk.linia(d.x, d.krzywe[k], { kolor: d.kolor || K.koral });
      leg.unshift({ tekst: wstaw(d.etykieta_krzywej), kolor: d.kolor || K.koral });
      (d.punkty || []).forEach(function (p) {
        wyk.punkty(p.x, p.y, { kolor: p.kolor, r: p.r || 5 });
        leg.push({ tekst: p.etykieta, kolor: p.kolor, typ: "punkt" });
      });
      wyk.odklip();
      wyk.legenda(leg, d.legenda || "prawo");
      if (info) info.innerHTML = d.info[k];
    };
    wyk.rysuj();
  };

  /* =====================================================================
     2. Pole kierunków budowane strzałka po strzałce + przewidywanie końca trajektorii
     ===================================================================== */
  RRZ.W.pole_losowe = function (root, d) {
    szkielet(root, d.tytul, d.opis);
    var N = d.strzalki.length, n = d.start_strzalek || 0;
    var startIdx = d.start_trajektorii || 0, przewid = null, odsloniete = 0, anim = null;
    var wyk = new Wykres(root, { proporcja: 0.58, maksWys: 500 });
    var r1 = el("div", "rrz-w-rzad", root);
    var s = suwak(r1, {
      etykieta: "Liczba strzałek:", min: 0, max: N, krok: 1, wartosc: n,
      format: function (v) { return v + " / " + N; }, zmiana: function (v) { n = v; wyk.rysuj(); }
    });
    function ustawN(v) { n = Math.max(0, Math.min(N, v)); s.ustaw(n); wyk.rysuj(); }
    przycisk(r1, "+1 strzałka", function () { ustawN(n + 1); });
    przycisk(r1, "+10", function () { ustawN(n + 10); });
    przycisk(r1, "wszystkie", function () { ustawN(N); });
    przycisk(r1, "wyczyść", function () { ustawN(0); });
    var r2 = el("div", "rrz-w-rzad", root);
    var etStart = el("span", null, r2);
    przycisk(r2, "Losuj nowy start", function () {
      var nowy; do { nowy = Math.floor(Math.random() * d.trajektorie.T.length); } while (nowy === startIdx && d.trajektorie.T.length > 1);
      startIdx = nowy; przewid = null; odsloniete = 0; if (anim) cancelAnimationFrame(anim); odswiezInfo(); wyk.rysuj();
    });
    var bSprawdz = przycisk(r2, "Sprawdź!", function () {
      if (anim) cancelAnimationFrame(anim);
      var t0 = null;
      function krok(ts) {
        if (t0 === null) t0 = ts;
        odsloniete = Math.min(1, (ts - t0) / 1400);
        wyk.rysuj();
        if (odsloniete < 1) anim = requestAnimationFrame(krok); else odswiezInfo();
      }
      anim = requestAnimationFrame(krok);
    }, "rrz-akcent");
    var info = el("div", "rrz-w-info", root);
    var tk = d.xlim[1];
    function koniecPrawdziwy() { var T = d.trajektorie.T[startIdx]; return T[T.length - 1]; }
    function odswiezInfo() {
      var T0 = d.trajektorie.T[startIdx][0];
      etStart.innerHTML = "Start: <b>T(0) = " + liczba(T0, 0) + d.jednostka + "</b>";
      bSprawdz.disabled = przewid === null;
      if (przewid === null) {
        info.innerHTML = "Kliknij na wykresie wysokość, na której Twoim zdaniem trajektoria z punktu startowego skończy się w chwili <b>t = " +
          liczba(tk, 0) + " " + d.jednostka_x + "</b>. Potem naciśnij <b>Sprawdź!</b>";
      } else if (odsloniete < 1) {
        info.innerHTML = "Twoje przewidywanie: <b>" + liczba(przewid, 1) + d.jednostka + "</b>. Możesz jeszcze poprawić – kliknij ponownie.";
      } else {
        var p = koniecPrawdziwy(), blad = Math.abs(przewid - p);
        info.innerHTML = "Twoje przewidywanie: <b>" + liczba(przewid, 1) + d.jednostka + "</b>, naprawdę: <b>" + liczba(p, 1) + d.jednostka +
          "</b> – " + (blad < 3 ? "<span class='rrz-dobrze'>świetnie, pomyłka tylko " + liczba(blad, 1) + d.jednostka + "!</span>"
            : blad < 8 ? "<span class='rrz-dobrze'>nieźle, pomyłka " + liczba(blad, 1) + d.jednostka + ".</span>"
              : "<span class='rrz-zle'>pomyłka " + liczba(blad, 1) + d.jednostka + ". Spójrz, jak trajektoria „płynie” wzdłuż strzałek.</span>");
      }
    }
    wyk.cv.style.cursor = "crosshair";
    wyk.cv.addEventListener("click", function (e) {
      var r = wyk.cv.getBoundingClientRect();
      var y = wyk.odwrotnieY(e.clientY - r.top);
      if (y < d.ylim[0] || y > d.ylim[1]) return;
      przewid = y; odsloniete = 0; if (anim) cancelAnimationFrame(anim); odswiezInfo(); wyk.rysuj();
    });
    wyk.rysuj = function () {
      if (!wyk.W) return;
      wyk.zakres(d.xlim[0], d.xlim[1], d.ylim[0], d.ylim[1]);
      wyk.rama({ xEtykieta: d.xlabel, yEtykieta: d.ylabel });
      var k = wyk.pxNaJedn(), dl = Math.min(d.dx * k[0], d.dy * k[1]) * 0.78;
      wyk.klip();
      wyk.pozioma(d.rownowaga, { kolor: K.fiolet, kreski: [2, 5], grubosc: 1.2, alfa: 0.7 });
      for (var i = 0; i < n; i++) {
        var a = d.strzalki[i], ost = i === n - 1;
        wyk.strzalka(a[0], a[1], 1, a[2], { dl: ost ? dl * 1.1 : dl, kolor: ost ? K.koral : K.granat, alfa: ost ? 1 : 0.62, grubosc: ost ? 2.2 : 1.5 });
      }
      var tt = d.trajektorie.t, TT = d.trajektorie.T[startIdx];
      if (odsloniete > 0) {
        var ile = Math.max(2, Math.round(odsloniete * tt.length));
        wyk.linia(tt.slice(0, ile), TT.slice(0, ile), { kolor: K.morski, grubosc: 3.2 });
        if (odsloniete >= 1) wyk.punkty([tt[tt.length - 1]], [TT[TT.length - 1]], { kolor: K.morski, r: 7 });
      }
      wyk.pionowa(tk, { kolor: K.piasek, kreski: [4, 4], grubosc: 1.4 });
      if (przewid !== null) {
        wyk.linia([d.xlim[0], tk], [przewid, przewid], { kolor: K.koral, kreski: [3, 5], grubosc: 1.4, alfa: 0.7 });
        var c = wyk.ctx, X = wyk.X(tk), Y = wyk.Y(przewid);
        c.save(); c.fillStyle = K.koral; c.strokeStyle = "#fff"; c.lineWidth = 2;
        c.beginPath(); c.moveTo(X, Y - 9); c.lineTo(X + 9, Y); c.lineTo(X, Y + 9); c.lineTo(X - 9, Y); c.closePath(); c.fill(); c.stroke(); c.restore();
        wyk.tekst(tk, przewid, "Twoje przewidywanie", { wyrown: "right", dx: -14, dy: -12, kolor: K.koral, waga: "600", tlo: "#fff" });
      }
      wyk.odklip();
      wyk.punkty([tt[0]], [TT[0]], { kolor: K.koral, r: 7.5, obrysGr: 2.5 });
      wyk.tekst(tt[0], TT[0], "START", { dx: 12, dy: -12, kolor: K.koral, waga: "700", tlo: "#fff" });
    };
    odswiezInfo();
    wyk.rysuj();
  };

  /* =====================================================================
     3. Metoda Eulera: łamana dla n kroków (policzona w Pythonie) vs rozwiązanie dokładne
     ===================================================================== */
  RRZ.W.euler = function (root, d) {
    szkielet(root, d.tytul, d.opis);
    var i = d.start || 0, pole = true;
    var wyk = new Wykres(root, { proporcja: 0.56, maksWys: 480 });
    var r = el("div", "rrz-w-rzad", root);
    suwak(r, {
      etykieta: "Liczba kroków n =", min: 0, max: d.ns.length - 1, krok: 1, wartosc: i,
      format: function (v) { return d.ns[v] + "  (h = " + liczba(d.xlim[1] / d.ns[v], d.xlim[1] / d.ns[v] < 2 ? 2 : 1) + " " + d.jednostka_x + ")"; },
      zmiana: function (v) { i = v; wyk.rysuj(); }
    });
    if (d.pole) przelacznik(r, "pole kierunków", true, function (s) { pole = s; wyk.rysuj(); });
    var info = el("div", "rrz-w-info", root);
    wyk.rysuj = function () {
      if (!wyk.W) return;
      wyk.zakres(d.xlim[0], d.xlim[1], d.ylim[0], d.ylim[1]);
      wyk.rama({ xEtykieta: d.xlabel, yEtykieta: d.ylabel });
      wyk.klip();
      if (pole && d.pole) {
        var k = wyk.pxNaJedn(), dl = Math.min(d.pole.dx * k[0], d.pole.dy * k[1]) * 0.75;
        d.pole.strzalki.forEach(function (a) { wyk.strzalka(a[0], a[1], 1, a[2], { dl: dl, alfa: 0.55 }); });
      }
      wyk.linia(d.dokladne.t, d.dokladne.T, { kolor: K.morski, grubosc: 3 });
      var t = d.t[i], T = d.T[i];
      wyk.linia(t, T, { kolor: K.koral, grubosc: 2.6 });
      if (t.length <= 61) wyk.punkty(t, T, { kolor: K.koral, r: t.length > 30 ? 3.5 : 5 });
      wyk.odklip();
      wyk.legenda([{ tekst: "rozwiązanie dokładne", kolor: K.morski }, { tekst: (d.etykieta || "metoda Eulera") + ", n = " + d.ns[i], kolor: K.koral }]);
      var dok = d.dokladne.T[d.dokladne.T.length - 1], wyn = T[T.length - 1];
      info.innerHTML = "Po " + liczba(d.xlim[1], 0) + " " + d.jednostka_x + ": Euler daje <b>" + liczba(wyn, 2) + d.jednostka +
        "</b>, dokładnie <b>" + liczba(dok, 2) + d.jednostka + "</b>, błąd: <b>" + liczba(Math.abs(wyn - dok), 2) + d.jednostka + "</b>" +
        (d.ns[i] === d.kartka ? " &nbsp;← <b style='color:#e76f51'>tyle kroków robiliście na kartce!</b>" : "");
    };
    wyk.rysuj();
  };

  /* =====================================================================
     4. Meteoroid: dwa modele, zmienna wysokość startowa (policzone w Pythonie)
     ===================================================================== */
  RRZ.W.meteoroid = function (root, d) {
    szkielet(root, d.tytul, d.opis);
    var i = d.start || 0;
    var kol = el("div", "rrz-w-kolumny", root);
    var lewa = el("div", null, kol), prawa = el("div", null, kol);
    lewa.style.flex = "1.6 1 360px";
    var wyk = new Wykres(lewa, { proporcja: 0.66, maksWys: 430 });
    var wyk2 = new Wykres(prawa, { proporcja: 0.9, maksWys: 430, margines: { l: 52, r: 12 } });
    var r = el("div", "rrz-w-rzad", root);
    suwak(r, {
      etykieta: "Wysokość startowa:", min: 0, max: d.wysokosci.length - 1, krok: 1, wartosc: i,
      format: function (v) { return d.etykiety[v]; },
      zmiana: function (v) { i = v; wyk.rysuj(); wyk2.rysuj(); }
    });
    var info = el("div", "rrz-w-info", root);
    function czas(s) { return s < 120 ? liczba(s, 0) + " s" : s < 7200 ? liczba(s / 60, 1) + " min" : liczba(s / 3600, 2) + " h"; }
    wyk.rysuj = function () {
      if (!wyk.W) return;
      var J = d.jablkowy[i], N = d.newton[i];
      var tmax = Math.max(J.t[J.t.length - 1], N.t[N.t.length - 1]);
      var dziel = tmax < 180 ? 1 : 60, jedn = tmax < 180 ? "s" : "min";
      var h0 = d.wysokosci[i];
      wyk.zakres(0, tmax / dziel * 1.03, 0, h0 * 1.08);
      wyk.rama({ xEtykieta: "czas [" + jedn + "]", yEtykieta: "wysokość [km]", tytul: "Start z " + d.etykiety[i] });
      wyk.klip();
      wyk.linia(J.t.map(function (x) { return x / dziel; }), J.h, { kolor: K.koral });
      wyk.linia(N.t.map(function (x) { return x / dziel; }), N.h, { kolor: K.granat });
      wyk.odklip();
      wyk.legenda([{ tekst: "model „jabłkowy” (g stałe)", kolor: K.koral }, { tekst: "model Newtona", kolor: K.granat }]);
      var rozT = (N.czas - J.czas) / N.czas * 100, rozV = (J.v - N.v) / N.v * 100;
      info.innerHTML = "<table class='rrz-w-tabela'><tr><th></th><th>czas spadania</th><th>prędkość uderzenia</th></tr>" +
        "<tr><td>model „jabłkowy”</td><td>" + czas(J.czas) + "</td><td>" + liczba(J.v / 1000, 2) + " km/s</td></tr>" +
        "<tr><td>model Newtona</td><td>" + czas(N.czas) + "</td><td>" + liczba(N.v / 1000, 2) + " km/s</td></tr>" +
        "<tr><td><b>rozbieżność</b></td><td><b>" + liczba(rozT, 1) + "%</b></td><td><b>" + liczba(rozV, 1) + "%</b></td></tr></table>";
    };
    wyk2.rysuj = function () {
      if (!wyk2.W) return;
      var hs = d.wysokosci, roz = d.jablkowy.map(function (J, j) { return (d.newton[j].czas - J.czas) / d.newton[j].czas * 100; });
      var ymax = Math.max(60, Math.ceil(Math.max.apply(null, roz) / 10) * 10);
      wyk2.zakres(hs[0] * 0.7, hs[hs.length - 1] * 1.4, 0, ymax, true);
      var tick = [10, 100, 1000, 10000, 100000].filter(function (v) { return v >= hs[0] * 0.7 && v <= hs[hs.length - 1] * 1.4; });
      wyk2.rama({ xEtykieta: "wysokość startowa [km] (skala log.)", yEtykieta: "rozbieżność czasu [%]", tytul: "Im wyżej, tym gorzej",
        xTicki: tick, formatX: function (v) { return v >= 1000 ? (v / 1000) + " tys." : String(v); } });
      wyk2.linia(hs.slice(0, i + 1), roz.slice(0, i + 1), { kolor: K.fiolet, grubosc: 2 });
      wyk2.linia(hs, roz, { kolor: K.fiolet, grubosc: 1.2, alfa: 0.25 });
      wyk2.punkty(hs.slice(0, i + 1), roz.slice(0, i + 1), { kolor: K.fiolet, r: 3.5, obrys: null });
      wyk2.punkty([hs[i]], [roz[i]], { kolor: K.koral, r: 7 });
    };
    wyk.rysuj(); wyk2.rysuj();
  };

  /* =====================================================================
     5. Pole kierunków układu 2D (Lotka–Volterra) – liczone w przeglądarce
     ===================================================================== */
  function rk4_2d(f, x, y, h, kroki, granica) {
    var X = [x], Y = [y];
    for (var i = 0; i < kroki; i++) {
      var k1 = f(x, y), k2 = f(x + h / 2 * k1[0], y + h / 2 * k1[1]), k3 = f(x + h / 2 * k2[0], y + h / 2 * k2[1]), k4 = f(x + h * k3[0], y + h * k3[1]);
      x += h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]); y += h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]);
      X.push(x); Y.push(y);
      if (!isFinite(x) || !isFinite(y) || Math.abs(x) > granica || Math.abs(y) > granica) break;
    }
    return [X, Y];
  }
  RRZ.rk4_2d = rk4_2d;
  RRZ.W.lotka_volterra = function (root, d) {
    szkielet(root, d.tytul, d.opis);
    var p = {};
    d.parametry.forEach(function (q) { p[q.klucz] = q.wartosc; });
    var krzywe = false, wlasny = null;
    var wyk = new Wykres(root, { proporcja: 0.6, maksWys: 500 });
    var wykT = null;
    var r = el("div", "rrz-w-rzad", root);
    d.parametry.forEach(function (q) {
      suwak(r, {
        etykieta: q.nazwa, min: q.min, max: q.max, krok: q.krok, wartosc: q.wartosc,
        format: function (v) { return liczba(v, q.cyfry == null ? 2 : q.cyfry); },
        zmiana: function (v) { p[q.klucz] = v; rysujWszystko(); }
      });
    });
    var r2 = el("div", "rrz-w-rzad", root);
    przelacznik(r2, "Pokaż krzywe fazowe", false, function (s) {
      krzywe = s; boxT.style.display = s ? "" : "none"; if (s && wykT) setTimeout(wykT.rozmiar, 0); rysujWszystko();
    });
    przycisk(r2, "Przywróć parametry", function () {
      d.parametry.forEach(function (q) { p[q.klucz] = q.wartosc; });
      Array.prototype.forEach.call(r.querySelectorAll("input"), function (inp, j) { inp.value = d.parametry[j].wartosc; inp.dispatchEvent(new Event("input")); });
    });
    var wsk = el("span", null, r2); wsk.style.cssText = "font-size:14px;color:#5b6b7c";
    wsk.innerHTML = "Gdy krzywe są włączone, kliknij na wykresie, aby wypuścić własną.";
    var boxT = el("div", null, root); boxT.style.display = "none";
    wykT = new Wykres(boxT, { proporcja: 0.3, maksWys: 230, minWys: 170, margines: { t: 26, b: 42 } });
    var info = el("div", "rrz-w-info", root);
    function f(x, y) { return [p.a * x - p.b * x * y, p.d * x * y - p.c * y]; }
    function starty() {
      var ex = p.c / p.d, ey = p.a / p.b;
      return (d.mnozniki || [1.2, 1.5, 2.0, 2.7]).map(function (m) { return [ex, ey * m]; });
    }
    function trajektoria(s) { return rk4_2d(f, s[0], s[1], d.krok_czasu || 0.01, Math.round((d.czas || 30) / (d.krok_czasu || 0.01)), 1e6); }
    var paleta = [K.morski, K.fiolet, K.piasek, K.granat];
    wyk.cv.addEventListener("click", function (e) {
      if (!krzywe) return;
      var b = wyk.cv.getBoundingClientRect();
      var x = wyk.odwrotnieX(e.clientX - b.left), y = wyk.odwrotnieY(e.clientY - b.top);
      if (x <= 0 || y <= 0) return;
      wlasny = [x, y]; rysujWszystko();
    });
    wyk.rysuj = function () {
      if (!wyk.W) return;
      wyk.zakres(d.xlim[0], d.xlim[1], d.ylim[0], d.ylim[1]);
      wyk.rama({ xEtykieta: d.xlabel, yEtykieta: d.ylabel });
      wyk.cv.style.cursor = krzywe ? "crosshair" : "default";
      var nx = d.siatka[0], ny = d.siatka[1], dx = (d.xlim[1] - d.xlim[0]) / nx, dy = (d.ylim[1] - d.ylim[0]) / ny;
      var k = wyk.pxNaJedn(), dl = Math.min(dx * k[0], dy * k[1]) * 0.72;
      var pola = [], vmax = 0;
      for (var i = 0; i < nx; i++) for (var j = 0; j < ny; j++) {
        var x = d.xlim[0] + (i + 0.5) * dx, y = d.ylim[0] + (j + 0.5) * dy, v = f(x, y), s = Math.hypot(v[0] * k[0], v[1] * k[1]);
        pola.push([x, y, v, s]); vmax = Math.max(vmax, s);
      }
      wyk.klip();
      pola.forEach(function (q) {
        var w = Math.pow(q[3] / vmax, 0.35);
        wyk.strzalka(q[0], q[1], q[2][0], q[2][1], { dl: dl, kolor: K.granat, alfa: 0.25 + 0.55 * w, grubosc: 1.4 });
      });
      var ex = p.c / p.d, ey = p.a / p.b;
      if (krzywe) {
        starty().forEach(function (s, i) { var tr = trajektoria(s); wyk.linia(tr[0], tr[1], { kolor: paleta[i % paleta.length], grubosc: 2.4 }); });
        if (wlasny) { var tr = trajektoria(wlasny); wyk.linia(tr[0], tr[1], { kolor: K.koral, grubosc: 3.6 }); wyk.punkty([wlasny[0]], [wlasny[1]], { kolor: K.koral, r: 6 }); }
        wyk.punkty([ex], [ey], { kolor: K.zloty, r: 6.5, obrys: K.granat });
        wyk.tekst(ex, ey, "równowaga", { dx: 10, dy: 12, kolor: K.granat, waga: "600", tlo: "#fff" });
      }
      wyk.odklip();
      info.innerHTML = d.rownanie + " &nbsp; Punkt równowagi: zające <b>" + liczba(ex, 1) + "</b>, lisy <b>" + liczba(ey, 1) + "</b>.";
    };
    wykT.rysuj = function () {
      if (!wykT.W || !krzywe) return;
      var s = wlasny || starty()[1], tr = trajektoria(s), h = d.krok_czasu || 0.01;
      var t = tr[0].map(function (_, i) { return i * h; });
      var ymax = Math.max(Math.max.apply(null, tr[0]), Math.max.apply(null, tr[1])) * 1.1;
      wykT.zakres(0, t[t.length - 1], 0, ymax || 1);
      wykT.rama({ xEtykieta: "czas", tytul: "Ta sama " + (wlasny ? "(Twoja) " : "") + "krzywa w czasie" });
      wykT.linia(t, tr[0], { kolor: K.morski, grubosc: 2.2 });
      wykT.linia(t, tr[1], { kolor: K.koral, grubosc: 2.2 });
      wykT.legenda([{ tekst: d.nazwa_x, kolor: K.morski }, { tekst: d.nazwa_y, kolor: K.koral }]);
    };
    function rysujWszystko() { wyk.rysuj(); wykT.rysuj(); }
    rysujWszystko();
  };

  /* =====================================================================
     6. Zagadnienie trzech ciał – animacja (całkowanie RK4 ze zmiennym krokiem w przeglądarce)
     ===================================================================== */
  function przyspieszenia(m, s) {
    var n = m.length, a = [], rmin = Infinity;
    for (var i = 0; i < n; i++) a.push([0, 0]);
    for (i = 0; i < n; i++) for (var j = i + 1; j < n; j++) {
      var dx = s[j][0] - s[i][0], dy = s[j][1] - s[i][1], r2 = dx * dx + dy * dy, r = Math.sqrt(r2), r3 = r2 * r;
      rmin = Math.min(rmin, r / Math.pow(m[i] + m[j], 1 / 3));
      a[i][0] += m[j] * dx / r3; a[i][1] += m[j] * dy / r3; a[j][0] -= m[i] * dx / r3; a[j][1] -= m[i] * dy / r3;
    }
    return [a, rmin];
  }
  function Uklad(m, r, v) {
    this.m = m.slice(); this.n = m.length; this.t = 0;
    this.s = r.map(function (q) { return q.slice(); }).concat(v.map(function (q) { return q.slice(); }));
    this.slady = r.map(function (q) { return [q.slice()]; });
  }
  Uklad.prototype.pochodna = function (s) {
    var n = this.n, a = przyspieszenia(this.m, s.slice(0, n))[0];
    return s.slice(n).concat(a);
  };
  Uklad.prototype.krok = function (h) {
    var s = this.s, self = this;
    function dod(u, k, c) { return u.map(function (q, i) { return [q[0] + c * k[i][0], q[1] + c * k[i][1]]; }); }
    var k1 = this.pochodna(s), k2 = this.pochodna(dod(s, k1, h / 2)), k3 = this.pochodna(dod(s, k2, h / 2)), k4 = this.pochodna(dod(s, k3, h));
    this.s = s.map(function (q, i) {
      return [q[0] + h / 6 * (k1[i][0] + 2 * k2[i][0] + 2 * k3[i][0] + k4[i][0]), q[1] + h / 6 * (k1[i][1] + 2 * k2[i][1] + 2 * k3[i][1] + k4[i][1])];
    });
    this.t += h;
  };
  Uklad.prototype.dojdz = function (T, eta, maxSlad, prog) {
    var n = this.n, licz = 0;
    while (this.t < T && licz < 40000) {
      var rmin = przyspieszenia(this.m, this.s.slice(0, n))[1];
      var h = Math.min(0.004, eta * Math.pow(rmin, 1.5), T - this.t + 1e-12);
      this.krok(h); licz++;
      for (var i = 0; i < n; i++) {
        var sl = this.slady[i], o = sl[sl.length - 1], q = this.s[i];
        if (Math.hypot(q[0] - o[0], q[1] - o[1]) > prog) { sl.push(q.slice()); if (sl.length > maxSlad) sl.shift(); }
      }
    }
  };
  RRZ.W.trzy_ciala = function (root, d) {
    szkielet(root, d.tytul, d.opis);
    var nr = 0, tempo = 1, zab = 0, gra = false, widoczny = false, ostatni = null;
    var A, B, zasiegAkt = 1;
    var wyk = new Wykres(root, { proporcja: 0.62, maksWys: 560, margines: { l: 8, r: 8, t: 8, b: 8 } });
    var r1 = el("div", "rrz-w-rzad", root);
    var bUkl = d.uklady.map(function (u, i) {
      return przycisk(r1, u.nazwa, function () { nr = i; bUkl.forEach(function (b, j) { b.classList.toggle("rrz-on", j === i); }); start(); });
    });
    bUkl[0].classList.add("rrz-on");
    var bGraj = przycisk(r1, "▶ graj", function () {
      var u = d.uklady[nr]; if (!gra && u.t_max && A.t >= u.t_max) { start(); gra = true; bGraj.innerHTML = "❚❚ pauza"; return; }
      gra = !gra; bGraj.innerHTML = gra ? "❚❚ pauza" : "▶ graj"; }, "rrz-akcent");
    przycisk(r1, "↺ od nowa", function () { start(); });
    var r2 = el("div", "rrz-w-rzad", root);
    suwak(r2, { etykieta: "Tempo:", min: 0.25, max: 4, krok: 0.25, wartosc: 1, format: function (v) { return liczba(v, 2) + "×"; }, zmiana: function (v) { tempo = v; } });
    var ZAB = d.zaburzenia;
    suwak(r2, {
      etykieta: "Bliźniak przesunięty o:", min: 0, max: ZAB.length - 1, krok: 1, wartosc: 0,
      format: function (v) { return ZAB[v] === 0 ? "brak bliźniaka" : liczba(ZAB[v], Math.max(0, -Math.floor(Math.log10(ZAB[v])))); },
      zmiana: function (v) { zab = ZAB[v]; start(); }
    });
    var info = el("div", "rrz-w-info", root);
    function start() {
      var u = d.uklady[nr];
      A = new Uklad(u.m, u.r, u.v); zasiegAkt = u.zasieg;
      if (zab > 0) { var r = u.r.map(function (q) { return q.slice(); }); r[0][0] += zab; B = new Uklad(u.m, r, u.v); } else B = null;
      wyk.rysuj();
    }
    var kol = d.kolory || [K.koral, K.morski, K.zloty];
    function rysujUklad(U, u, cien) {
      var c = wyk.ctx, sk = wyk.skala, cx = wyk.W / 2, cy = wyk.H / 2;
      function P(q) { return [cx + q[0] * sk, cy - q[1] * sk]; }
      for (var i = 0; i < U.n; i++) {
        var sl = U.slady[i];
        c.save(); c.strokeStyle = kol[i]; c.lineWidth = cien ? 1.4 : 2; c.lineJoin = "round";
        if (cien) c.setLineDash([4, 4]);
        var kawalek = 60;
        for (var a = 0; a < sl.length - 1; a += kawalek) {
          c.globalAlpha = (cien ? 0.5 : 0.9) * Math.pow((a + kawalek) / sl.length, 1.4);
          c.beginPath(); var p0 = P(sl[a]); c.moveTo(p0[0], p0[1]);
          for (var b = a + 1; b <= Math.min(a + kawalek, sl.length - 1); b++) { var pb = P(sl[b]); c.lineTo(pb[0], pb[1]); }
          c.stroke();
        }
        c.restore();
        var q = P(U.s[i]), rr = 4 + 4.5 * Math.cbrt(u.m[i] / Math.max.apply(null, u.m));
        c.save(); c.globalAlpha = cien ? 0.55 : 1;
        if (!cien) { var g = c.createRadialGradient(q[0], q[1], 0, q[0], q[1], rr * 2.6); g.addColorStop(0, kol[i] + "66"); g.addColorStop(1, kol[i] + "00"); c.fillStyle = g; c.beginPath(); c.arc(q[0], q[1], rr * 2.6, 0, 7); c.fill(); }
        c.fillStyle = cien ? "#fff" : kol[i]; c.strokeStyle = cien ? kol[i] : "#fff"; c.lineWidth = 2;
        c.beginPath(); c.arc(q[0], q[1], cien ? rr * 0.8 : rr, 0, 7); c.fill(); c.stroke();
        c.restore();
      }
    }
    wyk.rysuj = function () {
      if (!wyk.W || !A) return;
      var u = d.uklady[nr], c = wyk.ctx;
      var dal = 0; for (var q = 0; q < A.n; q++) dal = Math.max(dal, Math.abs(A.s[q][0]) * wyk.H / wyk.W, Math.abs(A.s[q][1]));
      zasiegAkt = Math.max(zasiegAkt, Math.min(dal * 1.12, u.zasieg * 6));
      wyk.skala = Math.min(wyk.W, wyk.H) / 2 / zasiegAkt;
      var g = c.createRadialGradient(wyk.W / 2, wyk.H / 2, 0, wyk.W / 2, wyk.H / 2, Math.max(wyk.W, wyk.H) * 0.7);
      g.addColorStop(0, "#22385a"); g.addColorStop(1, "#0f1c2e");
      c.fillStyle = g; c.fillRect(0, 0, wyk.W, wyk.H);
      // gwiazdy w tle (stały wzór)
      c.fillStyle = "rgba(255,255,255,.35)";
      for (var i = 0; i < 70; i++) { var x = (Math.sin(i * 91.7) * 0.5 + 0.5) * wyk.W, y = (Math.sin(i * 47.3 + 1) * 0.5 + 0.5) * wyk.H; c.fillRect(x, y, 1.2, 1.2); }
      if (B) rysujUklad(B, u, true);
      rysujUklad(A, u, false);
      c.font = "600 14px " + FONT; c.fillStyle = "#e3e8ee"; c.textBaseline = "top";
      c.fillText(u.nazwa + "   t = " + liczba(A.t, 1), 14, 12);
      c.font = "13px " + FONT; c.fillStyle = "#a5b1be";
      c.fillText("masy: " + u.m.join(" : "), 14, 32);
      var tekst = u.opis + (!gra && A.t === 0 ? " Naciśnij <b>▶ graj</b>, aby uruchomić symulację." : "") + (u.t_max && A.t >= u.t_max ? " <b>Koniec symulacji</b> – naciśnij ▶, aby obejrzeć jeszcze raz." : "");
      if (B) {
        var odl = 0; for (var k = 0; k < A.n; k++) odl = Math.max(odl, Math.hypot(A.s[k][0] - B.s[k][0], A.s[k][1] - B.s[k][1]));
        tekst += "<br>Największa odległość ciała od swojego bliźniaka: <b>" + (odl < 0.001 ? odl.toExponential(1).replace(".", ",") : liczba(odl, 3)) + "</b>" +
          (odl > 0.5 ? " – <span class='rrz-zle'>symulacje całkiem się rozjechały!</span>" : "");
      }
      info.innerHTML = tekst;
    };
    function petla(ts) {
      if (!root.isConnected) return;
      requestAnimationFrame(petla);
      if (ostatni === null) ostatni = ts;
      var dt = Math.min(0.05, (ts - ostatni) / 1000); ostatni = ts;
      if (!gra || !widoczny || !A) return;
      var u = d.uklady[nr], T = A.t + dt * tempo * (u.tempo || 1);
      if (u.t_max && A.t >= u.t_max) { gra = false; bGraj.innerHTML = "▶ graj"; return; }
      A.dojdz(T, d.eta || 0.003, 2500, u.zasieg / 300);
      if (B) B.dojdz(T, d.eta || 0.003, 2500, u.zasieg / 300);
      wyk.rysuj();
    }
    if (window.IntersectionObserver) new IntersectionObserver(function (e) { widoczny = e[0].isIntersecting; }).observe(root);
    else widoczny = true;
    start();
    requestAnimationFrame(petla);
  };
})();
"""

__all__ = ["widget_krzywe", "widget_pole_kierunkow", "widget_euler", "widget_meteoroid",
           "widget_lotka_volterra", "widget_trzy_ciala"]


def _zaokr(x, cyfry=3):
    """Zamienia tablice numpy na listy liczb zaokrąglonych (mniejszy plik HTML)."""
    if isinstance(x, dict):
        return {k: _zaokr(v, cyfry) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_zaokr(v, cyfry) for v in x]
    if isinstance(x, np.ndarray):
        return _zaokr(x.tolist(), cyfry)
    if isinstance(x, (float, np.floating)):
        x = float(x)
        return round(x, cyfry) if np.isfinite(x) else None
    if isinstance(x, np.integer):
        return int(x)
    return x


def _pokaz(nazwa, dane, cyfry=3):
    uid = "rrz-" + uuid.uuid4().hex[:10]
    dane_json = json.dumps(_zaokr(dane, cyfry), ensure_ascii=False, separators=(",", ":"))
    kod = (f'<div id="{uid}" class="rrz-w">Ładowanie widgetu… (jeśli ten napis nie znika, uruchom komórkę ponownie)</div>\n'
           f'<script>\n{_JS}\n'
           f'(function(){{var s=document.currentScript;'
           f'var el=(s&&s.parentNode&&s.parentNode.querySelector("#{uid}"))||document.getElementById("{uid}");'
           f'RRZ.W.{nazwa}(el,{dane_json});}})();\n</script>')
    display(HTML(kod))


def _etykieta(v, cyfry):
    return f"{v:.{cyfry}f}".replace(".", ",")


# ---------------------------------------------------------------------------
def widget_krzywe(x, krzywe, parametry, *, xlim, ylim, xlabel, ylabel, etykieta_krzywej,
                  tytuly=None, punkty=(), poziome=(), pozioma_param=None, info=None,
                  tytul=None, opis=None, legenda="prawo", kolor=None, cyfry=2):
    """Wykres krzywej zależnej od parametrów ustawianych suwakami.

    krzywe     – słownik {(indeksy parametrów): tablica y} albo lista w kolejności „wierszowej”
    parametry  – lista słowników {"nazwa": "k =", "wartosci": [...], "cyfry": 4, "start": indeks}
    """
    par = []
    for p in parametry:
        w = list(p["wartosci"])
        par.append({"nazwa": p["nazwa"], "wartosci": w, "start": p.get("start", 0),
                    "etykiety": p.get("etykiety") or [_etykieta(v, p.get("cyfry", 2)) for v in w]})
    dane = dict(x=x, krzywe=list(krzywe), parametry=par, xlim=xlim, ylim=ylim, xlabel=xlabel, ylabel=ylabel,
                etykieta_krzywej=etykieta_krzywej, tytuly=tytuly, punkty=list(punkty), poziome=list(poziome),
                pozioma_param=pozioma_param, info=info, tytul=tytul, opis=opis, legenda=legenda, kolor=kolor)
    _pokaz("krzywe", dane, cyfry)


def widget_pole_kierunkow(strzalki, t, trajektorie, *, xlim, ylim, dx, dy, rownowaga,
                          xlabel="czas [min]", ylabel="temperatura [°C]", jednostka="°C", jednostka_x="min",
                          start_trajektorii=0, start_strzalek=1, tytul=None, opis=None):
    """Pole kierunków odsłaniane strzałka po strzałce + zgadywanie końca trajektorii.

    strzalki    – lista [t, T, nachylenie] w kolejności, w jakiej mają się pojawiać
    t           – wspólna oś czasu trajektorii
    trajektorie – lista tablic T(t) dla różnych punktów startowych
    """
    dane = dict(strzalki=strzalki, trajektorie={"t": t, "T": list(trajektorie)}, xlim=xlim, ylim=ylim, dx=dx, dy=dy,
                rownowaga=rownowaga, xlabel=xlabel, ylabel=ylabel, jednostka=jednostka, jednostka_x=jednostka_x,
                start_trajektorii=start_trajektorii, start_strzalek=start_strzalek, tytul=tytul, opis=opis)
    _pokaz("pole_losowe", dane, 3)


def widget_euler(wyniki, t_dokladne, T_dokladne, *, xlim, ylim, pole=None, kartka=None, start=None,
                 xlabel="czas [min]", ylabel="temperatura [°C]", jednostka="°C", jednostka_x="min",
                 etykieta="metoda Eulera", tytul=None, opis=None):
    """Łamana Eulera dla różnej liczby kroków n (suwak) na tle rozwiązania dokładnego.

    wyniki – słownik {n: (t, x)} – wyniki funkcji euler(...) policzone w notatniku
    pole   – opcjonalnie słownik {"strzalki": [[t, T, nachylenie], ...], "dx": ..., "dy": ...}
    """
    ns = sorted(wyniki)
    dane = dict(ns=ns, t=[wyniki[n][0] for n in ns], T=[wyniki[n][1] for n in ns],
                dokladne={"t": t_dokladne, "T": T_dokladne}, xlim=xlim, ylim=ylim, pole=pole, kartka=kartka,
                start=ns.index(start) if start in ns else 0, xlabel=xlabel, ylabel=ylabel, jednostka=jednostka,
                jednostka_x=jednostka_x, etykieta=etykieta, tytul=tytul, opis=opis)
    _pokaz("euler", dane, 3)


def _przerzedz(t, h, ile=250):
    t, h = np.asarray(t), np.asarray(h)
    if len(t) > ile:
        i = np.unique(np.linspace(0, len(t) - 1, ile).astype(int))
        t, h = t[i], h[i]
    return t, h


def widget_meteoroid(wysokosci_km, jablkowy, newton, *, start=0, tytul=None, opis=None):
    """Porównanie dwóch modeli spadku dla różnych wysokości startowych.

    jablkowy, newton – listy wyników (czasy [s], wysokości [m], prędkość końcowa [m/s]) dla kolejnych wysokości
    """
    def pakuj(w):
        czasy, wys, v = w
        t, h = _przerzedz(czasy, np.asarray(wys) / 1000)
        return {"t": t, "h": h, "czas": float(czasy[-1]), "v": float(v)}
    etykiety = [f"{h:,.0f} km".replace(",", " ") for h in wysokosci_km]
    dane = dict(wysokosci=list(wysokosci_km), etykiety=etykiety, jablkowy=[pakuj(w) for w in jablkowy],
                newton=[pakuj(w) for w in newton], start=start, tytul=tytul, opis=opis)
    _pokaz("meteoroid", dane, 2)


def widget_lotka_volterra(a, b, c, d, *, xlim=(0, 100), ylim=(0, 60), siatka=(22, 14), czas=40,
                          tytul=None, opis=None):
    """Pole kierunków modelu drapieżnik–ofiara; parametry podaje się jako (wartość, min, max, krok)."""
    def par(klucz, nazwa, q):
        return {"klucz": klucz, "nazwa": nazwa, "wartosc": q[0], "min": q[1], "max": q[2], "krok": q[3], "cyfry": 3}
    dane = dict(parametry=[par("a", "rozmnażanie zajęcy a =", a), par("b", "skuteczność polowań b =", b),
                           par("c", "umieranie lisów c =", c), par("d", "zysk lisów z zająca d =", d)],
                xlim=xlim, ylim=ylim, siatka=siatka, czas=czas, krok_czasu=0.01,
                xlabel="zające Z [tys.]", ylabel="lisy L [setki]", nazwa_x="zające", nazwa_y="lisy",
                rownanie="Z′ = a·Z − b·Z·L, &nbsp; L′ = d·Z·L − c·L.", tytul=tytul, opis=opis)
    _pokaz("lotka_volterra", dane, 4)


def widget_trzy_ciala(uklady, *, zaburzenia=(0, 1e-6, 1e-4, 1e-2), tytul=None, opis=None):
    """Animacja zagadnienia trzech ciał (G = 1). Każdy układ: nazwa, opis, m, r, v, zasieg, tempo."""
    _pokaz("trzy_ciala", dict(uklady=list(uklady), zaburzenia=list(zaburzenia), tytul=tytul, opis=opis), 10)
