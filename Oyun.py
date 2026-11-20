import json
import math
import random
from array import array
from dataclasses import dataclass, field
from pathlib import Path

import pygame

KLASOR = Path(__file__).resolve().parent
VARLIKLAR = KLASOR / "YemekCanavarı"
REKOR_DOSYASI = KLASOR / "rekor.json"

GENISLIK, YUKSEKLIK = 800, 600
FPS = 60
UST_BANT = 70
OYUN_ALANI = pygame.Rect(0, UST_BANT, GENISLIK, YUKSEKLIK - UST_BANT)

BASLANGIC_SURESI = 30.0
EN_COK_SURE = 40.0
SEVIYE_SURE_ODULU = 5.0
KOMBO_PENCERESI = 1.3  # saniye
EN_COK_KOMBO = 5
CARPMA_CEZASI = 4.0
KORUMA_SURESI = 1.5

BEYAZ = (255, 255, 255)
SOLUK = (190, 195, 215)
SIYAH = (0, 0, 0)
KIRMIZI = (255, 95, 95)
ALTIN = (255, 205, 60)
MAVI = (140, 200, 255)
PANEL = (12, 14, 28)


@dataclass
class EsyaTuru:
    ad: str
    puan: int
    sure: float
    omur: float
    agirlik: int
    aciklama: str
    renk: tuple


TURLER = {
    "mama": EsyaTuru("Mama", 1, 1.2, None, 6, "+1 puan, +1.2 sn", (205, 145, 60)),
    "kemik": EsyaTuru("Kemik", 2, 0.8, 9.0, 4, "+2 puan, +0.8 sn", (245, 238, 215)),
    "altin": EsyaTuru("Altın kemik", 5, 2.0, 4.5, 1, "+5 puan, +2 sn, çabuk kaybolur", ALTIN),
    "saat": EsyaTuru("Saat", 0, 5.0, 6.0, 1, "+5 sn", MAVI),
    "cikolata": EsyaTuru("Çikolata", 0, -3.0, 8.0, 2, "-3 sn, komboyu bozar", (130, 75, 40)),
}


@dataclass
class Tema:
    ad: str
    ust: tuple
    alt: tuple
    sus: tuple
    vurgu: tuple
    zerre: str
    zerre_rengi: tuple
    zerre_sayisi: int


TEMALAR = (
    Tema("Bahçe", (118, 186, 84), (86, 156, 64), (64, 128, 48), (150, 235, 120),
         "polen", (255, 245, 170), 30),
    Tema("Park", (74, 142, 72), (52, 116, 56), (38, 92, 44), (110, 220, 130),
         "yaprak", (215, 160, 70), 22),
    Tema("Gün Batımı", (214, 160, 98), (168, 104, 72), (140, 96, 64), (255, 175, 90),
         "toz", (255, 220, 170), 35),
    Tema("Gece", (30, 62, 58), (16, 34, 44), (22, 48, 44), (140, 170, 255),
         "ates_bocegi", (220, 255, 120), 28),
    Tema("Fırtına", (72, 96, 88), (48, 68, 70), (84, 112, 132), (175, 195, 255),
         "yagmur", (185, 205, 255), 90),
)

YENILIKLER = {
    1: "Mamaları ve kemikleri topla!",
    2: "Çikolata çıktı, yeme! İlk kirpi geldi.",
    3: "Altın kemik çıktı. Köpek büyüdü!",
    4: "Saat çıktı. Arılar seni kovalıyor!",
    5: "Fırtına: herkes hızlandı!",
}


@dataclass
class SeviyeAyari:
    esya_sayisi: int
    kirpi: int
    ari: int
    dusman_hizi: float
    oyuncu_hizi: float
    sure_hizi: float
    turler: tuple
    yenilik: str


def seviye_esigi(seviye):
    n = seviye - 1
    return 8 * n + n * (n - 1)


def seviye_hesapla(toplanan):
    seviye = 1
    while toplanan >= seviye_esigi(seviye + 1):
        seviye += 1
    return seviye


def seviye_ayari(seviye):
    turler = ["mama", "kemik"]
    if seviye >= 2:
        turler.append("cikolata")
    if seviye >= 3:
        turler.append("altin")
    if seviye >= 4:
        turler.append("saat")
    return SeviyeAyari(
        esya_sayisi=min(2 + seviye // 2, 5),
        kirpi=min(seviye - 1, 4),
        ari=0 if seviye < 4 else min(seviye - 3, 3),
        dusman_hizi=min(110 + 25 * (seviye - 1), 330),
        oyuncu_hizi=min(280 + 15 * (seviye - 1), 420),
        sure_hizi=min(1 + 0.08 * (seviye - 1), 1.5),
        turler=tuple(turler),
        yenilik=YENILIKLER.get(seviye, "Herkes biraz daha hızlandı!"),
    )


def tema_sec(seviye):
    return TEMALAR[min(seviye, len(TEMALAR)) - 1]


def kombo_hesapla(kombo, son_yeme, simdi):
    if simdi - son_yeme <= KOMBO_PENCERESI:
        return min(kombo + 1, EN_COK_KOMBO)
    return 1


def tur_sec(turler):
    return random.choices(turler, weights=[TURLER[t].agirlik for t in turler])[0]


def rekor_oku():
    try:
        return int(json.loads(REKOR_DOSYASI.read_text())["rekor"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def rekor_yaz(rekor):
    try:
        REKOR_DOSYASI.write_text(json.dumps({"rekor": rekor}))
    except OSError:
        pass


def ton_uret(f0, f1, sure, ses=0.35, dalga="sinus"):
    ayar = pygame.mixer.get_init()
    if ayar is None or ayar[1] != -16:
        return None
    frekans, _, kanal = ayar
    n = int(frekans * sure)
    ornekler = array("h")
    faz = 0.0
    for i in range(n):
        oran = i / n
        faz += 2 * math.pi * (f0 + (f1 - f0) * oran) / frekans
        deger = math.sin(faz)
        if dalga == "kare":
            deger = 0.6 if deger >= 0 else -0.6
        zarf = min(1.0, i / (frekans * 0.01)) * (1 - oran)
        ornekler.extend([int(32767 * ses * deger * zarf)] * kanal)
    return pygame.mixer.Sound(buffer=ornekler.tobytes())


class Sesler:

    def __init__(self):
        self.sessiz = False
        self.efektler = {}
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(str(VARLIKLAR / "ArkaPlan.mp3"))
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)
            self.efektler = {
                "ye": pygame.mixer.Sound(str(VARLIKLAR / "yeme.mp3")),
                "seviye": pygame.mixer.Sound(str(VARLIKLAR / "LevelUp.mp3")),
                "altin": ton_uret(880, 1760, 0.18, 0.25),
                "saat": ton_uret(660, 990, 0.15, 0.25),
                "kotu": ton_uret(300, 120, 0.25),
                "carpma": ton_uret(180, 60, 0.3, 0.3, "kare"),
            }
        except pygame.error:
            self.efektler = {}

    def cal(self, ad):
        ses = self.efektler.get(ad)
        if ses is not None and not self.sessiz:
            ses.play()

    def sessiz_degistir(self):
        self.sessiz = not self.sessiz
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(0 if self.sessiz else 0.45)


def daire_resim(resim, boyut, zemin):
    yuzey = pygame.Surface((boyut, boyut), pygame.SRCALPHA)
    merkez = boyut // 2
    pygame.draw.circle(yuzey, zemin, (merkez, merkez), merkez)
    olcekli = pygame.transform.smoothscale(resim, (boyut, boyut))
    maske = pygame.Surface((boyut, boyut), pygame.SRCALPHA)
    pygame.draw.circle(maske, (255, 255, 255, 255), (merkez, merkez), merkez - 2)
    olcekli.blit(maske, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    yuzey.blit(olcekli, (0, 0))
    pygame.draw.circle(yuzey, BEYAZ, (merkez, merkez), merkez, 3)
    return yuzey


def kemik_ciz(renk, kenar):
    s = pygame.Surface((38, 20), pygame.SRCALPHA)
    for rnk, b in ((kenar, 1), (renk, 0)):
        pygame.draw.rect(s, rnk, (8, 7 - b, 22, 6 + 2 * b), border_radius=3)
        for cx in (8, 30):
            for cy in (6, 13):
                pygame.draw.circle(s, rnk, (cx, cy), 5 + b)
    return pygame.transform.rotate(s, 25)


def saat_ciz():
    s = pygame.Surface((32, 34), pygame.SRCALPHA)
    kenar = (60, 110, 220)
    for x in (8, 24):
        pygame.draw.circle(s, kenar, (x, 6), 4)
    pygame.draw.circle(s, kenar, (16, 19), 14)
    pygame.draw.circle(s, BEYAZ, (16, 19), 11)
    pygame.draw.line(s, (40, 40, 60), (16, 19), (16, 11), 2)
    pygame.draw.line(s, (40, 40, 60), (16, 19), (22, 19), 2)
    pygame.draw.circle(s, (220, 60, 60), (16, 19), 2)
    return s


def cikolata_ciz():
    s = pygame.Surface((32, 26), pygame.SRCALPHA)
    pygame.draw.rect(s, (70, 40, 20), (1, 1, 30, 24), border_radius=4)
    pygame.draw.rect(s, (110, 62, 32), (3, 3, 26, 20), border_radius=3)
    for x in (4, 12):
        for y in (4, 13):
            pygame.draw.rect(s, (135, 80, 45), (x, y, 7, 8), border_radius=2)
    pygame.draw.rect(s, (205, 40, 55), (19, 0, 13, 26), border_radius=3)
    pygame.draw.line(s, (235, 235, 240), (22, 2), (22, 23), 2)
    return s


def kirpi_ciz():
    s = pygame.Surface((50, 40), pygame.SRCALPHA)
    cx, cy = 22, 22
    for k in range(13):
        a = math.radians(70 + k * 15)
        uc = (cx + math.cos(a) * 19, cy - math.sin(a) * 17)
        sol = (cx + math.cos(a - 0.2) * 9, cy - math.sin(a - 0.2) * 8)
        sag = (cx + math.cos(a + 0.2) * 9, cy - math.sin(a + 0.2) * 8)
        pygame.draw.polygon(s, (55, 38, 25), (sol, uc, sag))
    pygame.draw.ellipse(s, (125, 88, 58), (7, 13, 30, 20))
    for x in (13, 27):
        pygame.draw.ellipse(s, (60, 40, 25), (x, 30, 7, 5))
    pygame.draw.circle(s, (225, 195, 155), (35, 24), 7)
    pygame.draw.circle(s, SIYAH, (42, 25), 3)
    pygame.draw.circle(s, SIYAH, (34, 20), 2)
    pygame.draw.circle(s, BEYAZ, (34, 19), 1)
    return s


def ari_ciz(kanat_yukarida):
    s = pygame.Surface((40, 32), pygame.SRCALPHA)
    kanat = pygame.Surface((40, 32), pygame.SRCALPHA)
    if kanat_yukarida:
        pygame.draw.ellipse(kanat, (235, 245, 255, 170), (11, 0, 11, 15))
        pygame.draw.ellipse(kanat, (235, 245, 255, 170), (18, 1, 11, 14))
    else:
        pygame.draw.ellipse(kanat, (235, 245, 255, 170), (8, 6, 15, 8))
        pygame.draw.ellipse(kanat, (235, 245, 255, 170), (17, 6, 15, 8))
    pygame.draw.polygon(s, (40, 30, 10), ((3, 20), (9, 17), (9, 23)))
    pygame.draw.ellipse(s, (250, 200, 40), (7, 12, 24, 16))
    for x in (13, 20):
        pygame.draw.rect(s, (35, 30, 20), (x, 13, 3, 14))
    pygame.draw.circle(s, (35, 30, 20), (31, 19), 6)
    pygame.draw.circle(s, BEYAZ, (33, 17), 2)
    s.blit(kanat, (0, 0))
    return s


def parilti_ciz(renk, yaricap):
    s = pygame.Surface((yaricap * 2, yaricap * 2), pygame.SRCALPHA)
    for r in range(yaricap, 0, -1):
        pygame.draw.circle(s, (*renk, int(120 * (1 - r / yaricap))), (yaricap, yaricap), r)
    return s


def zemin_ciz(tema, tohum):
    rnd = random.Random(tohum)
    s = pygame.Surface((GENISLIK, YUKSEKLIK))
    for y in range(YUKSEKLIK):
        oran = y / YUKSEKLIK
        renk = [int(a + (b - a) * oran) for a, b in zip(tema.ust, tema.alt)]
        pygame.draw.line(s, renk, (0, y), (GENISLIK, y))

    doku = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
    for _ in range(2500):
        ton = rnd.choice(((0, 0, 0, 22), (255, 255, 255, 14)))
        doku.fill(ton, (rnd.randrange(GENISLIK), rnd.randrange(YUKSEKLIK), 2, 2))

    if tema.zerre == "ates_bocegi":  # ay ışığı
        for r in range(260, 0, -8):
            pygame.draw.ellipse(doku, (180, 210, 255, 4), (400 - r * 1.4, 330 - r, r * 2.8, r * 2))
    if tema.zerre == "yaprak":  # ağaçlar
        for _ in range(9):
            x = rnd.choice((rnd.randint(-60, 70), rnd.randint(730, 860)))
            y = rnd.randint(40, 640)
            r = rnd.randint(55, 95)
            pygame.draw.circle(doku, (20, 50, 25, 90), (x + 12, y + 14), r)
            pygame.draw.circle(doku, (34, 92, 42, 255), (x, y), r)
            pygame.draw.circle(doku, (52, 124, 56, 255), (x - r // 4, y - r // 4), r // 2)
    if tema.zerre == "yagmur":  # su birikintileri
        for _ in range(8):
            w, h = rnd.randint(60, 140), rnd.randint(22, 46)
            x, y = rnd.randint(0, GENISLIK - w), rnd.randint(UST_BANT, YUKSEKLIK - h)
            pygame.draw.ellipse(doku, (*tema.sus, 200), (x, y, w, h))
            pygame.draw.ellipse(doku, (190, 210, 230, 90), (x + w // 5, y + h // 5, w // 3, h // 4))
    if tema.zerre == "toz":  # taşlar
        for _ in range(26):
            w = rnd.randint(8, 22)
            x, y = rnd.randrange(GENISLIK), rnd.randrange(UST_BANT, YUKSEKLIK)
            pygame.draw.ellipse(doku, (0, 0, 0, 40), (x + 2, y + 3, w, w * 2 // 3))
            pygame.draw.ellipse(doku, (*tema.sus, 255), (x, y, w, w * 2 // 3))

    for _ in range(170):  # otlar
        x, y = rnd.randrange(GENISLIK), rnd.randrange(UST_BANT, YUKSEKLIK)
        for dx, uzun in ((-4, 7), (0, 10), (4, 7)):
            pygame.draw.line(doku, (*tema.sus, 220), (x, y), (x + dx, y - uzun), 2)
    if tema.zerre == "polen":  # çiçekler
        for _ in range(45):
            x, y = rnd.randrange(GENISLIK), rnd.randrange(UST_BANT, YUKSEKLIK)
            yaprak = rnd.choice(((255, 255, 255), (255, 190, 215), (255, 230, 100), (190, 170, 255)))
            for ax, ay in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                pygame.draw.circle(doku, (*yaprak, 255), (x + ax, y + ay), 3)
            pygame.draw.circle(doku, (240, 180, 40, 255), (x, y), 2)
    s.blit(doku, (0, 0))
    return s


def vinyet_ciz():
    s = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
    for i in range(40):
        alfa = int(120 * (1 - i / 40) ** 2)
        pygame.draw.rect(s, (0, 0, 0, alfa), (i * 3, i * 3, GENISLIK - i * 6, YUKSEKLIK - i * 6), 3)
    return s


def yaz(hedef, font, metin, renk, golge=True, **konum):
    yuzey = font.render(metin, True, renk)
    alan = yuzey.get_rect(**konum)
    if golge:
        hedef.blit(font.render(metin, True, SIYAH), alan.move(2, 2))
    hedef.blit(yuzey, alan)
    return alan


def panel_ciz(hedef, alan, cerceve, alfa=200):
    s = pygame.Surface(alan.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*PANEL, alfa), s.get_rect(), border_radius=14)
    pygame.draw.rect(s, cerceve, s.get_rect(), 2, border_radius=14)
    hedef.blit(s, alan)


def cubuk_ciz(hedef, alan, oran, renk):
    pygame.draw.rect(hedef, (40, 44, 70), alan, border_radius=6)
    dolu = alan.copy()
    dolu.width = max(0, int(alan.width * max(0.0, min(1.0, oran))))
    if dolu.width:
        pygame.draw.rect(hedef, renk, dolu, border_radius=6)
    pygame.draw.rect(hedef, (90, 95, 130), alan, 1, border_radius=6)


class Gorseller:
    def __init__(self):
        def yukle(ad):
            return pygame.image.load(str(VARLIKLAR / ad)).convert_alpha()

        self.caylak = yukle("caylak.png")
        self.boss = yukle("boos.png")
        vinyet = vinyet_ciz()
        self.menu_arka = pygame.transform.smoothscale(
            pygame.image.load(str(VARLIKLAR / "arkaplan.jpg")).convert(), (GENISLIK, YUKSEKLIK)
        )
        self.menu_arka.blit(vinyet, (0, 0))
        self.arka_planlar = []
        for i, tema in enumerate(TEMALAR):
            zemin = zemin_ciz(tema, i)
            zemin.blit(vinyet, (0, 0))
            self.arka_planlar.append(zemin)

        self.ikonlar = {
            "mama": pygame.transform.smoothscale(yukle("yem.png"), (36, 26)),
            "kemik": kemik_ciz((245, 238, 215), (150, 130, 100)),
            "altin": kemik_ciz(ALTIN, (170, 110, 10)),
            "saat": saat_ciz(),
            "cikolata": cikolata_ciz(),
        }
        self.kirpi = kirpi_ciz()
        self.ari = (ari_ciz(True), ari_ciz(False))
        self.parilti = parilti_ciz(ALTIN, 30)

        self.dunya = pygame.Surface((GENISLIK, YUKSEKLIK))
        self.katman = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
        self.karartma = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
        self.karartma.fill((0, 0, 0, 140))

        yazi_tipi = "segoeui,dejavusans,arial"
        self.f_mini = pygame.font.SysFont(yazi_tipi, 15)
        self.f_kucuk = pygame.font.SysFont(yazi_tipi, 19)
        self.f_orta = pygame.font.SysFont(yazi_tipi, 26, bold=True)
        self.f_buyuk = pygame.font.SysFont(yazi_tipi, 34, bold=True)
        self.f_dev = pygame.font.SysFont(yazi_tipi, 64, bold=True)

        self._oyuncu_onbellek = {}
        self._golge_onbellek = {}

    def oyuncu(self, seviye, boyut):
        anahtar = (seviye >= 3, boyut)
        if anahtar not in self._oyuncu_onbellek:
            kaynak = self.boss if seviye >= 3 else self.caylak
            self._oyuncu_onbellek[anahtar] = daire_resim(kaynak, boyut, (250, 242, 225))
        return self._oyuncu_onbellek[anahtar]

    def golge(self, genislik):
        if genislik not in self._golge_onbellek:
            s = pygame.Surface((genislik, max(6, genislik // 3)), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, 80), s.get_rect())
            self._golge_onbellek[genislik] = s
        return self._golge_onbellek[genislik]


@dataclass
class Esya:
    tur: str
    x: float
    y: float
    yas: float = 0.0
    faz: float = field(default_factory=lambda: random.uniform(0, math.tau))
    yaricap: float = 15.0


@dataclass
class Dusman:
    x: float
    y: float
    vx: float
    vy: float
    ari: bool
    yaricap: float = 15.0


@dataclass
class Parcacik:
    x: float
    y: float
    vx: float
    vy: float
    omur: float
    toplam: float
    renk: tuple
    boyut: float
    yercekimi: float = 0.0


@dataclass
class UcanYazi:
    yuzey: pygame.Surface
    x: float
    y: float
    omur: float = 1.0


@dataclass
class Zerre:
    tip: str
    x: float
    y: float
    vx: float
    vy: float
    boyut: float
    faz: float


def zerre_uret(tip, ilk=True):
    asagi_iner = tip in ("yaprak", "yagmur")
    x = random.uniform(0, GENISLIK)
    if ilk:
        y = random.uniform(UST_BANT, YUKSEKLIK)
    else:
        y = UST_BANT - 10 if asagi_iner else YUKSEKLIK + 10
    if tip == "polen":
        vx, vy, b = random.uniform(-15, 15), random.uniform(-25, -8), random.uniform(1.5, 3)
    elif tip == "yaprak":
        vx, vy, b = random.uniform(20, 50), random.uniform(30, 60), random.uniform(3, 5)
    elif tip == "toz":
        vx, vy, b = random.uniform(-10, 10), random.uniform(-14, -4), random.uniform(1, 2.5)
    elif tip == "ates_bocegi":
        vx, vy, b = random.uniform(-20, 20), random.uniform(-20, 20), random.uniform(2, 3.5)
    else:  # yagmur
        vx, vy, b = -90.0, random.uniform(550, 700), 1.0
    return Zerre(tip, x, y, vx, vy, b, random.uniform(0, math.tau))


class Oyun:
    def __init__(self, gorseller, sesler):
        self.g = gorseller
        self.ses = sesler
        self.rekor = rekor_oku()
        self.zaman = 0.0
        self.yeni_oyun()
        self.durum = "menu"  # menu, oyun, durdu, bitti

    def yeni_oyun(self):
        self.skor = 0
        self.seviye = 1
        self.sure = BASLANGIC_SURESI
        self.kombo = 1
        self.son_yeme = -99.0
        self.en_iyi_kombo = 1
        self.toplanan = 0
        self.oyun_zamani = 0.0
        self.x, self.y = float(OYUN_ALANI.centerx), float(OYUN_ALANI.centery)
        self.vx = self.vy = 0.0
        self.yon = 1
        self.koruma = 0.0
        self.sarsinti = 0.0
        self.esyalar = []
        self.dusmanlar = []
        self.parcaciklar = []
        self.yazilar = []
        self.afis = None
        self.yeni_rekor = False
        self.dogum_sayaci = 0.0
        self._seviyeyi_kur()
        self.durum = "oyun"

    @property
    def ayar(self):
        return seviye_ayari(self.seviye)

    @property
    def tema(self):
        return tema_sec(self.seviye)

    @property
    def oyuncu_boyutu(self):
        return min(50 + 4 * (self.seviye - 1), 74)

    def _seviyeyi_kur(self):
        ayar = self.ayar
        kirpiler = [d for d in self.dusmanlar if not d.ari]
        arilar = [d for d in self.dusmanlar if d.ari]
        while len(kirpiler) < ayar.kirpi:
            kirpiler.append(self._dusman_uret(ari=False))
        while len(arilar) < ayar.ari:
            arilar.append(self._dusman_uret(ari=True))
        for d in kirpiler:
            hiz = math.hypot(d.vx, d.vy) or 1.0
            d.vx, d.vy = d.vx / hiz * ayar.dusman_hizi, d.vy / hiz * ayar.dusman_hizi
        self.dusmanlar = kirpiler + arilar
        self.zerreler = [zerre_uret(self.tema.zerre) for _ in range(self.tema.zerre_sayisi)]
        self.afis = [f"SEVİYE {self.seviye}", self.tema.ad, ayar.yenilik, 2.8]

    def _bos_konum(self, oyuncudan_uzak, kenar=30):
        x = y = 0.0
        for _ in range(60):
            x = random.uniform(OYUN_ALANI.left + kenar, OYUN_ALANI.right - kenar)
            y = random.uniform(OYUN_ALANI.top + kenar, OYUN_ALANI.bottom - kenar)
            if math.hypot(x - self.x, y - self.y) < oyuncudan_uzak:
                continue
            if any(math.hypot(x - e.x, y - e.y) < 50 for e in self.esyalar):
                continue
            break
        return x, y

    def _dusman_uret(self, ari):
        x, y = self._bos_konum(240)
        aci = random.uniform(0, math.tau)
        hiz = self.ayar.dusman_hizi * (0.3 if ari else 1.0)
        return Dusman(x, y, math.cos(aci) * hiz, math.sin(aci) * hiz, ari)

    def _esya_uret(self):
        iyi_var = any(TURLER[e.tur].puan > 0 for e in self.esyalar)
        tur = tur_sec(self.ayar.turler) if iyi_var else "mama"
        x, y = self._bos_konum(90)
        return Esya(tur, x, y)

    def tus(self, tus):
        baslat = tus in (pygame.K_RETURN, pygame.K_SPACE)
        if tus == pygame.K_m:
            self.ses.sessiz_degistir()
        elif self.durum == "menu":
            if baslat:
                self.yeni_oyun()
            elif tus == pygame.K_ESCAPE:
                return False
        elif self.durum == "oyun":
            if tus in (pygame.K_p, pygame.K_ESCAPE):
                self.durum = "durdu"
        elif self.durum == "durdu":
            if baslat or tus == pygame.K_p:
                self.durum = "oyun"
            elif tus == pygame.K_ESCAPE:
                self.durum = "menu"
        elif self.durum == "bitti":
            if baslat:
                self.yeni_oyun()
            elif tus == pygame.K_ESCAPE:
                self.durum = "menu"
        return True

    def odak_kayboldu(self):
        if self.durum == "oyun":
            self.durum = "durdu"

    def guncelle(self, dt, tuslar):
        if self.durum == "durdu":
            return
        self.zaman += dt
        self._zerreleri_guncelle(dt)
        self._efektleri_guncelle(dt)
        if self.durum != "oyun":
            return

        self.oyun_zamani += dt
        ayar = self.ayar
        self._oyuncuyu_hareket_ettir(dt, tuslar, ayar.oyuncu_hizi)

        r = self.oyuncu_boyutu / 2
        for e in list(self.esyalar):
            e.yas += dt
            omur = TURLER[e.tur].omur
            if omur is not None and e.yas >= omur:
                self.esyalar.remove(e)
                self._patlat(e.x, e.y, (200, 200, 200), 6, hiz=60)
            elif math.hypot(e.x - self.x, e.y - self.y) < r + e.yaricap:
                self._ye(e)

        self.dogum_sayaci -= dt
        if len(self.esyalar) < self.ayar.esya_sayisi and self.dogum_sayaci <= 0:
            self.esyalar.append(self._esya_uret())
            self.dogum_sayaci = 0.35

        self._dusmanlari_guncelle(dt, r)
        self.koruma = max(0.0, self.koruma - dt)

        self.sure -= dt * ayar.sure_hizi
        if self.sure <= 0:
            self._bitir()

    def _oyuncuyu_hareket_ettir(self, dt, tuslar, hiz):
        dx = int(tuslar[pygame.K_RIGHT] or tuslar[pygame.K_d]) - int(tuslar[pygame.K_LEFT] or tuslar[pygame.K_a])
        dy = int(tuslar[pygame.K_DOWN] or tuslar[pygame.K_s]) - int(tuslar[pygame.K_UP] or tuslar[pygame.K_w])
        uzunluk = math.hypot(dx, dy) or 1.0
        hedef_vx, hedef_vy = dx / uzunluk * hiz, dy / uzunluk * hiz
        yumusak = min(1.0, dt * 12)
        self.vx += (hedef_vx - self.vx) * yumusak
        self.vy += (hedef_vy - self.vy) * yumusak
        if dx:
            self.yon = dx
        r = self.oyuncu_boyutu / 2
        self.x = min(max(self.x + self.vx * dt, OYUN_ALANI.left + r), OYUN_ALANI.right - r)
        self.y = min(max(self.y + self.vy * dt, OYUN_ALANI.top + r), OYUN_ALANI.bottom - r)

    def _dusmanlari_guncelle(self, dt, oyuncu_r):
        hiz = self.ayar.dusman_hizi
        for d in self.dusmanlar:
            if d.ari:
                aci = math.atan2(self.y - d.y, self.x - d.x)
                donus = min(1.0, dt * 2.5)
                d.vx += (math.cos(aci) * hiz * 0.55 - d.vx) * donus
                d.vy += (math.sin(aci) * hiz * 0.55 - d.vy) * donus
            d.x += d.vx * dt
            d.y += d.vy * dt
            if d.x - d.yaricap < OYUN_ALANI.left:
                d.x, d.vx = OYUN_ALANI.left + d.yaricap, abs(d.vx)
            elif d.x + d.yaricap > OYUN_ALANI.right:
                d.x, d.vx = OYUN_ALANI.right - d.yaricap, -abs(d.vx)
            if d.y - d.yaricap < OYUN_ALANI.top:
                d.y, d.vy = OYUN_ALANI.top + d.yaricap, abs(d.vy)
            elif d.y + d.yaricap > OYUN_ALANI.bottom:
                d.y, d.vy = OYUN_ALANI.bottom - d.yaricap, -abs(d.vy)
            if self.koruma <= 0 and math.hypot(d.x - self.x, d.y - self.y) < oyuncu_r * 0.75 + d.yaricap:
                self._carp(d)

    def _ye(self, esya):
        tur = TURLER[esya.tur]
        self.esyalar.remove(esya)
        if tur.puan > 0:
            self.kombo = kombo_hesapla(self.kombo, self.son_yeme, self.oyun_zamani)
            self.son_yeme = self.oyun_zamani
            self.en_iyi_kombo = max(self.en_iyi_kombo, self.kombo)
            kazanc = tur.puan * self.kombo
            self.skor += kazanc
            self.toplanan += 1
            metin = f"+{kazanc}" + (f"  x{self.kombo}" if self.kombo > 1 else "")
            self._yazi(metin, esya.x, esya.y - 12, ALTIN if self.kombo > 1 else BEYAZ)
            self.ses.cal("altin" if esya.tur == "altin" else "ye")
        elif tur.sure < 0:
            self.kombo = 1
            self.sarsinti = 0.2
            self._yazi(f"{tur.sure:+.0f} sn", esya.x, esya.y - 12, KIRMIZI)
            self.ses.cal("kotu")
        else:
            self._yazi(f"+{tur.sure:.0f} sn", esya.x, esya.y - 12, MAVI)
            self.ses.cal("saat")
        self.sure = min(max(self.sure + tur.sure, 0.0), EN_COK_SURE)
        self._patlat(esya.x, esya.y, tur.renk, 14)

        yeni = seviye_hesapla(self.toplanan)
        if yeni > self.seviye:
            self._seviye_atla(yeni)

    def _seviye_atla(self, yeni):
        self.seviye = yeni
        self.sure = min(self.sure + SEVIYE_SURE_ODULU, EN_COK_SURE)
        self._seviyeyi_kur()
        self.ses.cal("seviye")
        renkler = (ALTIN, KIRMIZI, MAVI, self.tema.vurgu, BEYAZ)
        for _ in range(70):  # konfeti
            aci = random.uniform(0, math.tau)
            hiz = random.uniform(120, 380)
            omur = random.uniform(0.8, 1.6)
            self.parcaciklar.append(Parcacik(
                self.x, self.y, math.cos(aci) * hiz, math.sin(aci) * hiz - 150, omur, omur,
                random.choice(renkler), random.uniform(2.5, 5), yercekimi=420,
            ))
        self._yazi(f"+{SEVIYE_SURE_ODULU:.0f} sn", self.x, self.y - 45, MAVI)

    def _carp(self, dusman):
        self.sure = max(0.0, self.sure - CARPMA_CEZASI)
        self.kombo = 1
        self.koruma = KORUMA_SURESI
        self.sarsinti = 0.4
        self._yazi(f"-{CARPMA_CEZASI:.0f} sn", self.x, self.y - 35, KIRMIZI)
        self._patlat(self.x, self.y, (255, 80, 80), 20)
        self.ses.cal("carpma")
        aci = math.atan2(dusman.y - self.y, dusman.x - self.x)
        hiz = math.hypot(dusman.vx, dusman.vy) or self.ayar.dusman_hizi
        dusman.vx, dusman.vy = math.cos(aci) * hiz, math.sin(aci) * hiz

    def _bitir(self):
        self.sure = 0.0
        self.durum = "bitti"
        if self.skor > self.rekor:
            self.rekor = self.skor
            self.yeni_rekor = True
            rekor_yaz(self.rekor)

    def _patlat(self, x, y, renk, adet, hiz=170):
        for _ in range(adet):
            aci = random.uniform(0, math.tau)
            v = random.uniform(hiz * 0.4, hiz)
            omur = random.uniform(0.35, 0.7)
            self.parcaciklar.append(Parcacik(
                x, y, math.cos(aci) * v, math.sin(aci) * v, omur, omur, renk, random.uniform(2, 4.5)
            ))

    def _yazi(self, metin, x, y, renk):
        yuzey = self.g.f_orta.render(metin, True, renk)
        golge = self.g.f_orta.render(metin, True, SIYAH)
        birlesik = pygame.Surface((yuzey.get_width() + 2, yuzey.get_height() + 2), pygame.SRCALPHA)
        birlesik.blit(golge, (2, 2))
        birlesik.blit(yuzey, (0, 0))
        self.yazilar.append(UcanYazi(birlesik, x, max(y, UST_BANT + 60)))

    def _efektleri_guncelle(self, dt):
        for p in self.parcaciklar:
            p.omur -= dt
            p.vx *= 1 - min(1.0, 2.5 * dt)
            p.vy = p.vy * (1 - min(1.0, 2.5 * dt)) + p.yercekimi * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
        self.parcaciklar = [p for p in self.parcaciklar if p.omur > 0]
        for yazi in self.yazilar:
            yazi.omur -= dt
            yazi.y -= 45 * dt
        self.yazilar = [y for y in self.yazilar if y.omur > 0]
        if self.afis is not None:
            self.afis[3] -= dt
            if self.afis[3] <= 0:
                self.afis = None
        self.sarsinti = max(0.0, self.sarsinti - dt)

    def _zerreleri_guncelle(self, dt):
        for i, z in enumerate(self.zerreler):
            z.x += z.vx * dt
            z.y += z.vy * dt
            if z.tip == "ates_bocegi":
                z.x += math.sin(self.zaman * 2 + z.faz) * 25 * dt
                z.y += math.cos(self.zaman * 1.7 + z.faz) * 25 * dt
            if not (-20 < z.x < GENISLIK + 20 and UST_BANT - 20 < z.y < YUKSEKLIK + 20):
                self.zerreler[i] = zerre_uret(z.tip, ilk=z.tip == "ates_bocegi")

    def ciz(self, ekran):
        g = self.g
        dunya = g.dunya
        if self.durum == "menu":
            dunya.blit(g.menu_arka, (0, 0))
        else:
            dunya.blit(g.arka_planlar[TEMALAR.index(self.tema)], (0, 0))
        self._zerreleri_ciz(dunya)
        if self.durum != "menu":
            for e in self.esyalar:
                self._esya_ciz(dunya, e)
            for d in self.dusmanlar:
                self._dusman_ciz(dunya, d)
            self._oyuncu_ciz(dunya)
            self._efektleri_ciz(dunya)

        ox = oy = 0
        if self.sarsinti > 0 and self.durum == "oyun":
            m = 9 * self.sarsinti / 0.4
            ox, oy = random.uniform(-m, m), random.uniform(-m, m)
        ekran.fill(SIYAH)
        ekran.blit(dunya, (ox, oy))

        if self.durum == "menu":
            self._menu_ciz(ekran)
            return
        self._ust_bilgi_ciz(ekran)
        if self.afis is not None and self.durum == "oyun":
            self._afis_ciz(ekran)
        if self.durum == "durdu":
            self._durdu_ciz(ekran)
        elif self.durum == "bitti":
            self._bitti_ciz(ekran)

    def _zerreleri_ciz(self, dunya):
        katman = self.g.katman
        katman.fill((0, 0, 0, 0))
        renk = self.tema.zerre_rengi
        for z in self.zerreler:
            if z.tip == "yagmur":
                pygame.draw.line(katman, (*renk, 150), (z.x, z.y), (z.x - 5, z.y + 14), 1)
            elif z.tip == "yaprak":
                pygame.draw.ellipse(katman, (*renk, 200), (z.x, z.y, z.boyut * 2, z.boyut))
            elif z.tip == "ates_bocegi":
                parlak = 0.5 + 0.5 * math.sin(self.zaman * 4 + z.faz)
                pygame.draw.circle(katman, (*renk, int(50 * parlak)), (z.x, z.y), z.boyut * 3)
                pygame.draw.circle(katman, (*renk, int(80 + 170 * parlak)), (z.x, z.y), z.boyut)
            else:
                pygame.draw.circle(katman, (*renk, 150), (z.x, z.y), z.boyut)
        dunya.blit(katman, (0, 0))

    def _esya_ciz(self, dunya, e):
        omur = TURLER[e.tur].omur
        if omur is not None and omur - e.yas < 1.5 and int(self.zaman * 10) % 2 == 0:
            return
        ikon = self.g.ikonlar[e.tur]
        olcek = min(1.0, e.yas / 0.25)
        if olcek < 1.0:
            ikon = pygame.transform.rotozoom(ikon, 0, max(olcek, 0.05))
        sallanma = math.sin(self.zaman * 3 + e.faz) * 3
        golge = self.g.golge(26)
        dunya.blit(golge, golge.get_rect(center=(e.x, e.y + 16)))
        if e.tur == "altin":
            parilti = pygame.transform.rotozoom(self.g.parilti, 0, 1 + 0.15 * math.sin(self.zaman * 6))
            dunya.blit(parilti, parilti.get_rect(center=(e.x, e.y + sallanma)))
        dunya.blit(ikon, ikon.get_rect(center=(e.x, e.y + sallanma)))

    def _dusman_ciz(self, dunya, d):
        if d.ari:
            resim = self.g.ari[int(self.zaman * 20) % 2]
            sallanma = math.sin(self.zaman * 5 + d.x * 0.01) * 4
        else:
            resim = self.g.kirpi
            sallanma = -abs(math.sin(self.zaman * 10 + d.y * 0.01)) * 2
        if d.vx < 0:
            resim = pygame.transform.flip(resim, True, False)
        golge = self.g.golge(30)
        dunya.blit(golge, golge.get_rect(center=(d.x, d.y + 17)))
        dunya.blit(resim, resim.get_rect(center=(d.x, d.y + sallanma)))

    def _oyuncu_ciz(self, dunya):
        boyut = self.oyuncu_boyutu
        golge = self.g.golge(boyut)
        dunya.blit(golge, golge.get_rect(center=(self.x, self.y + boyut / 2)))
        if self.koruma > 0 and int(self.zaman * 15) % 2 == 0:
            return
        hareketli = math.hypot(self.vx, self.vy) > 30
        sallanma = math.sin(self.zaman * 14) * 3 if hareketli else math.sin(self.zaman * 3) * 1.5
        resim = self.g.oyuncu(self.seviye, boyut)
        if self.yon < 0:
            resim = pygame.transform.flip(resim, True, False)
        merkez = (self.x, self.y + sallanma)
        pygame.draw.circle(dunya, self.tema.vurgu, merkez, boyut / 2 + 3, 3)
        dunya.blit(resim, resim.get_rect(center=merkez))

    def _efektleri_ciz(self, dunya):
        katman = self.g.katman
        katman.fill((0, 0, 0, 0))
        for p in self.parcaciklar:
            alfa = int(255 * p.omur / p.toplam)
            pygame.draw.circle(katman, (*p.renk[:3], alfa), (p.x, p.y), p.boyut)
        dunya.blit(katman, (0, 0))
        for yazi in self.yazilar:
            yazi.yuzey.set_alpha(int(255 * min(1.0, yazi.omur * 2)))
            dunya.blit(yazi.yuzey, yazi.yuzey.get_rect(center=(yazi.x, yazi.y)))

    def _ust_bilgi_ciz(self, ekran):
        g = self.g
        tema = self.tema
        bant = pygame.Surface((GENISLIK, UST_BANT), pygame.SRCALPHA)
        bant.fill((*PANEL, 205))
        ekran.blit(bant, (0, 0))
        pygame.draw.line(ekran, tema.vurgu, (0, UST_BANT - 1), (GENISLIK, UST_BANT - 1), 2)

        yaz(ekran, g.f_mini, "SKOR", SOLUK, golge=False, topleft=(18, 8))
        yaz(ekran, g.f_buyuk, str(self.skor), BEYAZ, topleft=(16, 22))
        kalan_kombo = KOMBO_PENCERESI - (self.oyun_zamani - self.son_yeme)
        if self.kombo > 1 and kalan_kombo > 0:
            nabiz = 1 + 0.08 * math.sin(self.zaman * 12)
            yuzey = pygame.transform.rotozoom(g.f_orta.render(f"x{self.kombo} KOMBO", True, ALTIN), 0, nabiz)
            ekran.blit(yuzey, yuzey.get_rect(midleft=(120, 30)))
            cubuk_ciz(ekran, pygame.Rect(122, 50, 110, 6), kalan_kombo / KOMBO_PENCERESI, ALTIN)

        alt, ust = seviye_esigi(self.seviye), seviye_esigi(self.seviye + 1)
        yaz(ekran, g.f_kucuk, f"SEVİYE {self.seviye}  ·  {tema.ad}", tema.vurgu, midtop=(GENISLIK // 2, 6))
        cubuk = pygame.Rect(GENISLIK // 2 - 120, 36, 240, 14)
        cubuk_ciz(ekran, cubuk, (self.toplanan - alt) / (ust - alt), tema.vurgu)
        yaz(ekran, g.f_mini, f"sonraki seviyeye {ust - self.toplanan} yem", BEYAZ,
            center=(cubuk.centerx, cubuk.bottom + 10))

        kritik = self.sure < 8
        renk = KIRMIZI if kritik else ((120, 220, 120) if self.sure > 15 else ALTIN)
        if kritik and int(self.zaman * 4) % 2 == 0:
            renk = (255, 160, 160)
        yaz(ekran, g.f_orta, f"{self.sure:4.1f} sn", renk, topright=(GENISLIK - 18, 4))
        cubuk_ciz(ekran, pygame.Rect(GENISLIK - 228, 42, 210, 12), self.sure / EN_COK_SURE, renk)
        if self.ses.sessiz:
            yaz(ekran, g.f_mini, "SES KAPALI (M)", SOLUK, golge=False, topright=(GENISLIK - 240, 46))

    def _afis_ciz(self, ekran):
        baslik, tema_adi, aciklama, kalan = self.afis
        gecen = 2.8 - kalan
        alfa = int(255 * max(0.0, min(1.0, gecen / 0.3, kalan / 0.5)))
        kayma = int(-30 * max(0.0, 1 - gecen / 0.3))
        s = pygame.Surface((500, 124), pygame.SRCALPHA)
        panel_ciz(s, s.get_rect(), self.tema.vurgu, 200)
        yaz(s, self.g.f_dev, baslik, self.tema.vurgu, center=(250, 40))
        yaz(s, self.g.f_orta, tema_adi, BEYAZ, center=(250, 82))
        yaz(s, self.g.f_kucuk, aciklama, SOLUK, center=(250, 107))
        s.set_alpha(alfa)
        ekran.blit(s, s.get_rect(center=(GENISLIK // 2, 160 + kayma)))

    def _menu_ciz(self, ekran):
        g = self.g
        vurgu = TEMALAR[0].vurgu
        ekran.blit(g.karartma, (0, 0))
        sallanma = math.sin(self.zaman * 2) * 4
        yaz(ekran, g.f_dev, "YEM CANAVARI", ALTIN, center=(GENISLIK // 2, 62 + sallanma))
        yaz(ekran, g.f_kucuk, "Süre bitmeden topla; kirpilerden ve arılardan kaç!", BEYAZ,
            center=(GENISLIK // 2, 112))
        kopek = g.oyuncu(1, 84)
        ekran.blit(kopek, kopek.get_rect(center=(GENISLIK // 2, 175 + math.sin(self.zaman * 4) * 5)))

        panel = pygame.Rect(GENISLIK // 2 - 340, 228, 680, 262)
        panel_ciz(ekran, panel, vurgu)
        sol, sag = panel.left + 22, panel.centerx + 20
        yaz(ekran, g.f_kucuk, "TOPLA", vurgu, golge=False, topleft=(sol, panel.top + 12))
        for i, ad in enumerate(("mama", "kemik", "altin", "saat", "cikolata")):
            y = panel.top + 42 + i * 42
            ikon = g.ikonlar[ad]
            ekran.blit(ikon, ikon.get_rect(center=(sol + 18, y + 16)))
            tur = TURLER[ad]
            renk = KIRMIZI if tur.sure < 0 else BEYAZ
            yaz(ekran, g.f_kucuk, tur.ad, renk, golge=False, topleft=(sol + 46, y))
            yaz(ekran, g.f_mini, tur.aciklama, SOLUK, golge=False, topleft=(sol + 46, y + 20))

        yaz(ekran, g.f_kucuk, "KAÇ", KIRMIZI, golge=False, topleft=(sag, panel.top + 12))
        satirlar = (
            (g.kirpi, "Kirpi", f"Seviye 2'den sonra seker, değerse -{CARPMA_CEZASI:.0f} sn"),
            (g.ari[0], "Arı", "Seviye 4'ten sonra seni kovalar"),
        )
        for i, (resim, ad, aciklama) in enumerate(satirlar):
            y = panel.top + 42 + i * 42
            ekran.blit(resim, resim.get_rect(center=(sag + 18, y + 16)))
            yaz(ekran, g.f_kucuk, ad, BEYAZ, golge=False, topleft=(sag + 46, y))
            yaz(ekran, g.f_mini, aciklama, SOLUK, golge=False, topleft=(sag + 46, y + 20))

        yaz(ekran, g.f_kucuk, "İPUCU", ALTIN, golge=False, topleft=(sag, panel.top + 140))
        ipuclari = (
            f"{KOMBO_PENCERESI} sn içinde art arda ye: puan x{EN_COK_KOMBO}'e kadar katlanır.",
            f"Her seviye +{SEVIYE_SURE_ODULU:.0f} sn ve yeni bir şey getirir,",
            "ama süre her seviyede biraz daha hızlı akar.",
            "Seviye 3'te köpek büyür ve patron olur.",
        )
        for i, metin in enumerate(ipuclari):
            yaz(ekran, g.f_mini, metin, SOLUK, golge=False, topleft=(sag, panel.top + 166 + i * 22))

        yaz(ekran, g.f_mini, "Yön tuşları / WASD: hareket     P: duraklat     M: ses     Esc: çık",
            SOLUK, center=(GENISLIK // 2, 512))
        if int(self.zaman * 2) % 2 == 0:
            yaz(ekran, g.f_orta, "ENTER ile başla", vurgu, center=(GENISLIK // 2, 548))
        yaz(ekran, g.f_kucuk, f"Rekor: {self.rekor}", ALTIN, center=(GENISLIK // 2, 580))

    def _durdu_ciz(self, ekran):
        ekran.blit(self.g.karartma, (0, 0))
        yaz(ekran, self.g.f_dev, "DURAKLATILDI", BEYAZ, center=(GENISLIK // 2, YUKSEKLIK // 2 - 20))
        yaz(ekran, self.g.f_kucuk, "P veya Enter: devam     Esc: ana menü", SOLUK,
            center=(GENISLIK // 2, YUKSEKLIK // 2 + 40))

    def _bitti_ciz(self, ekran):
        g = self.g
        ekran.blit(g.karartma, (0, 0))
        panel = pygame.Rect(0, 0, 460, 330)
        panel.center = (GENISLIK // 2, YUKSEKLIK // 2 + 20)
        panel_ciz(ekran, panel, KIRMIZI, 225)
        cx = panel.centerx
        yaz(ekran, g.f_dev, "SÜRE DOLDU", KIRMIZI, center=(cx, panel.top + 48))
        yaz(ekran, g.f_buyuk, f"Skor: {self.skor}", BEYAZ, center=(cx, panel.top + 108))
        satirlar = (
            f"Seviye: {self.seviye} ({self.tema.ad})",
            f"Toplanan: {self.toplanan}",
            f"En iyi kombo: x{self.en_iyi_kombo}",
        )
        for i, metin in enumerate(satirlar):
            yaz(ekran, g.f_kucuk, metin, SOLUK, center=(cx, panel.top + 150 + i * 28))
        if self.yeni_rekor:
            nabiz = 1 + 0.08 * math.sin(self.zaman * 8)
            yuzey = pygame.transform.rotozoom(g.f_orta.render("YENİ REKOR!", True, ALTIN), 0, nabiz)
            ekran.blit(yuzey, yuzey.get_rect(center=(cx, panel.top + 248)))
        else:
            yaz(ekran, g.f_kucuk, f"Rekor: {self.rekor}", ALTIN, center=(cx, panel.top + 248))
        yaz(ekran, g.f_kucuk, "Enter: tekrar oyna     Esc: ana menü", BEYAZ, center=(cx, panel.top + 296))


def main():
    pygame.init()
    ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK))
    pygame.display.set_caption("Yem Canavarı")
    oyun = Oyun(Gorseller(), Sesler())
    pygame.display.set_icon(oyun.g.ikonlar["kemik"])
    saat = pygame.time.Clock()

    calisiyor = True
    while calisiyor:
        dt = min(saat.tick(FPS) / 1000, 0.05)
        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                calisiyor = False
            elif olay.type == pygame.KEYDOWN and not oyun.tus(olay.key):
                calisiyor = False
            elif olay.type == pygame.WINDOWFOCUSLOST:
                oyun.odak_kayboldu()
        oyun.guncelle(dt, pygame.key.get_pressed())
        oyun.ciz(ekran)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
