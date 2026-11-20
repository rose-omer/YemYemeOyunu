import json
import math
import random
from pathlib import Path

import pygame

KLASOR = Path(__file__).resolve().parent
VARLIKLAR = KLASOR / "YemekCanavarı"
REKOR_DOSYASI = KLASOR / "rekor.json"

GENISLIK, YUKSEKLIK = 800, 600
FPS = 60
SEVIYE_BASINA_YEM = 5
BASLANGIC_SURESI = 20.0
YEM_SURESI = 2.0
EN_COK_SURE = 30.0
BASLANGIC_HIZI = 270  # piksel/saniye
HIZ_ARTISI = 30  # her seviyede
EN_COK_HIZ = 600


def seviye_hesapla(skor):
    return skor // SEVIYE_BASINA_YEM + 1


def hiz_hesapla(seviye):
    return min(BASLANGIC_HIZI + HIZ_ARTISI * (seviye - 1), EN_COK_HIZ)


def yem_yerlestir(yem, karakter):
    """Yemi ekranda, karakterin üstüne gelmeyen rastgele bir yere koyar."""
    for _ in range(50):
        yem.x = random.randint(0, GENISLIK - yem.width)
        yem.y = random.randint(60, YUKSEKLIK - yem.height)
        if not yem.colliderect(karakter.inflate(80, 80)):
            return


def rekor_oku():
    try:
        return int(json.loads(REKOR_DOSYASI.read_text())["rekor"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def rekor_yaz(rekor):
    try:
        REKOR_DOSYASI.write_text(json.dumps({"rekor": rekor}))
    except OSError:
        pass  # rekor kaydedilemese de oyun devam eder


def sesleri_yukle():
    """Ses aygıtı yoksa oyun sessiz çalışır."""
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(str(VARLIKLAR / "ArkaPlan.mp3"))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        return (
            pygame.mixer.Sound(str(VARLIKLAR / "yeme.mp3")),
            pygame.mixer.Sound(str(VARLIKLAR / "LevelUp.mp3")),
        )
    except pygame.error:
        return None, None


def sesi_cal(ses):
    if ses is not None:
        ses.play()


def yaz(pencere, font, metin, renk, merkez=None, sol_ust=None):
    yuzey = font.render(metin, True, renk)
    konum = yuzey.get_rect()
    if merkez is not None:
        konum.center = merkez
    else:
        konum.topleft = sol_ust
    pencere.blit(yuzey, konum)


def main():
    pygame.init()
    pencere = pygame.display.set_mode((GENISLIK, YUKSEKLIK))
    pygame.display.set_caption("Yem Yeme Oyunu")

    yemeSesi, seviyeYukselme = sesleri_yukle()
    sessiz = False

    arkaPlan = pygame.transform.smoothscale(
        pygame.image.load(str(VARLIKLAR / "arkaplan.jpg")).convert(),
        (GENISLIK, YUKSEKLIK),
    )
    caylakResmi = pygame.image.load(str(VARLIKLAR / "caylak.png")).convert_alpha()
    boss = pygame.image.load(str(VARLIKLAR / "boos.png")).convert_alpha()
    yem = pygame.image.load(str(VARLIKLAR / "yem.png")).convert_alpha()

    kucukFont = pygame.font.SysFont("consolas,dejavusansmono,monospace", 28)
    font = pygame.font.SysFont("consolas,dejavusansmono,monospace", 48)
    buyukFont = pygame.font.SysFont("consolas,dejavusansmono,monospace", 72)

    saat = pygame.time.Clock()
    rekor = rekor_oku()

    def yeni_oyun():
        karakterKordinat = caylakResmi.get_rect(center=(GENISLIK // 2, YUKSEKLIK // 2))
        yemKordinat = yem.get_rect()
        yem_yerlestir(yemKordinat, karakterKordinat)
        return karakterKordinat, yemKordinat, 0, BASLANGIC_SURESI

    karakterKordinat, yemKordinat, skor, sure = yeni_oyun()
    karakter = caylakResmi
    durum = "oyun"  # oyun | durdu | bitti
    calisiyor = True

    while calisiyor:
        dt = saat.tick(FPS) / 1000

        for olay in pygame.event.get():
            if olay.type == pygame.QUIT:
                calisiyor = False
            elif olay.type == pygame.KEYDOWN:
                if olay.key == pygame.K_ESCAPE:
                    calisiyor = False
                elif olay.key == pygame.K_p and durum in ("oyun", "durdu"):
                    durum = "durdu" if durum == "oyun" else "oyun"
                elif olay.key == pygame.K_m:
                    sessiz = not sessiz
                    if pygame.mixer.get_init():
                        pygame.mixer.music.set_volume(0 if sessiz else 0.5)
                elif olay.key in (pygame.K_RETURN, pygame.K_SPACE) and durum == "bitti":
                    karakterKordinat, yemKordinat, skor, sure = yeni_oyun()
                    karakter = caylakResmi
                    durum = "oyun"

        seviye = seviye_hesapla(skor)

        if durum == "oyun":
            # yön verme (çapraz hareket dahil)
            tus = pygame.key.get_pressed()
            dx = int(tus[pygame.K_RIGHT] or tus[pygame.K_d]) - int(tus[pygame.K_LEFT] or tus[pygame.K_a])
            dy = int(tus[pygame.K_DOWN] or tus[pygame.K_s]) - int(tus[pygame.K_UP] or tus[pygame.K_w])
            if dx or dy:
                uzunluk = math.hypot(dx, dy)
                adim = hiz_hesapla(seviye) * dt
                karakterKordinat.x += round(dx / uzunluk * adim)
                karakterKordinat.y += round(dy / uzunluk * adim)
                karakterKordinat.clamp_ip(pygame.Rect(0, 0, GENISLIK, YUKSEKLIK))

            if karakterKordinat.colliderect(yemKordinat):
                if not sessiz:
                    sesi_cal(yemeSesi)
                skor += 1
                sure = min(sure + YEM_SURESI, EN_COK_SURE)
                yem_yerlestir(yemKordinat, karakterKordinat)

                if seviye_hesapla(skor) > seviye:
                    if not sessiz:
                        sesi_cal(seviyeYukselme)
                    if seviye_hesapla(skor) == 2:
                        merkez = karakterKordinat.center
                        karakter = boss
                        karakterKordinat = boss.get_rect(center=merkez)
                        karakterKordinat.clamp_ip(pygame.Rect(0, 0, GENISLIK, YUKSEKLIK))

            sure -= dt
            if sure <= 0:
                sure = 0
                durum = "bitti"
                if skor > rekor:
                    rekor = skor
                    rekor_yaz(rekor)

        # çizim
        pencere.blit(arkaPlan, (0, 0))
        pencere.blit(yem, yemKordinat)
        pencere.blit(karakter, karakterKordinat)

        yaz(pencere, font, f"Skor: {skor}", (255, 255, 255), sol_ust=(10, 8))
        yaz(pencere, kucukFont, f"Seviye {seviye_hesapla(skor)}   Rekor {rekor}",
            (255, 255, 255), sol_ust=(10, 62))
        sureRengi = (255, 90, 90) if sure < 5 else (255, 255, 255)
        yaz(pencere, font, f"{sure:4.1f} sn", sureRengi, sol_ust=(GENISLIK - 190, 8))

        if durum in ("durdu", "bitti"):
            kapak = pygame.Surface((GENISLIK, YUKSEKLIK), pygame.SRCALPHA)
            kapak.fill((0, 0, 0, 150))
            pencere.blit(kapak, (0, 0))
            orta = (GENISLIK // 2, YUKSEKLIK // 2)
            if durum == "durdu":
                yaz(pencere, buyukFont, "DURAKLATILDI", (255, 255, 255), merkez=orta)
                yaz(pencere, kucukFont, "P: devam   ESC: çık", (255, 255, 255),
                    merkez=(orta[0], orta[1] + 70))
            else:
                yaz(pencere, buyukFont, "OYUN BİTTİ", (255, 120, 120), merkez=(orta[0], orta[1] - 50))
                yaz(pencere, font, f"Skor: {skor}   Rekor: {rekor}", (255, 255, 255),
                    merkez=(orta[0], orta[1] + 20))
                yaz(pencere, kucukFont, "ENTER: tekrar oyna   ESC: çık", (255, 255, 255),
                    merkez=(orta[0], orta[1] + 80))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
