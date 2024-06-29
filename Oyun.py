import pygame
import random

pygame.init()

# pencere
genislik, yükseklik = 800, 600
pencere = pygame.display.set_mode((genislik, yükseklik))

# ses efektleri
pygame.mixer.music.load("ArkaPlan.mp3")
pygame.mixer.music.play(-1, 0.0)
yemeSesi = pygame.mixer.Sound("yeme.mp3")
seviyeYükselme = pygame.mixer.Sound("LevelUp.mp3")

hız = 10
saat = pygame.time.Clock()
FPS = 27

# karakter ve yem
karakter = pygame.image.load('caylak.png')
karakterKordinat = karakter.get_rect()
karakterKordinat.topleft = (genislik / 2, yükseklik / 2)

yem = pygame.image.load("yem.png")
yemKordinat = yem.get_rect()
yemKordinat.topleft = (150, 150)

arkaPlan = pygame.image.load("arkaplan.jpg")

font = pygame.font.SysFont("consolas", 64)

# skor
skor = 0
durum = True
y = 0

while durum:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            durum = False

    pencere.blit(arkaPlan, (0, 0))
    pencere.blit(karakter, karakterKordinat)
    pencere.blit(yem, yemKordinat)

    skorText = font.render(f"Skor: {skor}", True, (255, 255, 255))
    pencere.blit(skorText, (10, 10))
    pygame.display.flip()
    saat.tick(FPS)

    # yönVerme
    tus = pygame.key.get_pressed()
    if tus[pygame.K_LEFT] and karakterKordinat.left > 0:
        karakterKordinat.x -= hız
    elif tus[pygame.K_RIGHT] and karakterKordinat.right < genislik:
        karakterKordinat.x += hız
    elif tus[pygame.K_UP] and karakterKordinat.top > 0:
        karakterKordinat.y -= hız
    elif tus[pygame.K_DOWN] and karakterKordinat.bottom < yükseklik:
        karakterKordinat.y += hız

    if karakterKordinat.colliderect(yemKordinat):
        yemeSesi.play()
        yemKordinat.x = random.randint(0, genislik - 20)
        yemKordinat.y = random.randint(0, yükseklik - 20)
        skor += 1

    if skor > 5 and y == 0:
        karakter = pygame.image.load('boos.png')
        seviyeYükselme.play()
        karakterKordinat = karakter.get_rect()
        karakterKordinat.topleft = (300, 300)
        y += 1

pygame.quit()
