# Python İle Oyun: Yem Yeme Oyunu

Bu Python script'i, pygame kütüphanesi kullanılarak geliştirilmiş basit bir yem yeme oyununu temsil eder. Oyun, klavye yön tuşlarını kullanarak bir karakteri kontrol edip ekrandaki yemleri toplama üzerine kuruludur.

## Oyun Özellikleri
- Süre dolmadan yem topla: oyun 20 saniyeyle başlar, her yem 2 saniye ekler (en çok 30 sn).
- Her 5 yemde seviye atlanır; karakter hızlanır. İlk seviye atlamada karakterin görüntüsü değişir ve seviye yükselme sesi çalar.
- Süre bitince "Oyun bitti" ekranı çıkar. En yüksek skor (rekor) `rekor.json` dosyasına kaydedilir.
- Çapraz hareket, duraklatma ve sessiz mod vardır.
- Ekran 800x600'dür. Oyun hangi klasörden çalıştırılırsa çalıştırılsın dosyalarını bulur.

## Kurulum
1. Python 3.9 veya üstünü kurun.
2. Bağımlılığı yükleyin: `pip install -r requirements.txt`
3. Oyunu başlatın: `python Oyun.py`

## Kontroller
| Tuş | İşlev |
|---|---|
| Yön tuşları veya W A S D | Karakteri hareket ettir |
| P | Duraklat / devam |
| M | Sesi aç / kapat |
| Enter veya Boşluk | Oyun bittiğinde yeniden başlat |
| Esc | Çık |

## Geliştirici Bilgisi
Bu oyun, pygame kütüphanesi kullanılarak geliştirilmiş ve Python programlama diliyle yazılmıştır.

### Ekran Görüntüsü
  ![1](https://github.com/rose-omer/YemYemeOyunu/assets/117285777/ee6c668e-3282-466e-95aa-f5e8669c9eb7)
  ![2](https://github.com/rose-omer/YemYemeOyunu/assets/117285777/0dcfcb0f-2a16-4804-92a2-eee7729406f4)

#### Geliştirici
- Geliştirici: [ömer](https://www.instagram.com/bennomerrr/)
- GitHub: (https://github.com/rose-omer/)

