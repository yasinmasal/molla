# 2D motor — geliştirme dalı

Bu daldaki Actions, `studio_2d.py` ile Gemini metin/storyboard, Edge TTS, Pillow ve FFmpeg kullanır. Gemini görsel/video API'si çağrılmaz. Kodla çizilen 7 varlık (octopus, heart, planet, star, book, atom, bulb), 5 arka plan, 5 hareket ve 4 palet vardır. Model yalnız izin verilen JSON komutlarını kullanabilir; bilinmeyen komut, sahne süresi veya varlık reddedilir. Nesne kütüphanesi kapsamı sınırlıdır; tüm kavramları konuya özgü görselleştirmez. `samples/octopus.json` insan tarafından yazılmış test planıdır.

0–3, 3–10 ve 10–15 saniyelik sahneler; göz kırpan ahtapot, yüzen parçacıklar, hareketli figürler ve geçişler örneklenir. Kod kareleri FFmpeg stdin'e aktarır; kareler diske yığılmaz, işçi sayısı 1'dir. Ses sahneye sığmazsa TTS yeniden üretilmeden önce Gemini'den kısa cümle istenir; en çok 3 deneme, ses hızlandırma yok. Kapanış/başlık animasyonları, tam ses senkronu, konuşan dudaklar, 20–30 varlık, SVG kitaplığı, SQLite, UI ve 10 bilgi kalite testi henüz tamamlanmadı.

Yerel, sessiz ve AI gerektirmeyen örnek: `python -m animation.preview --plan samples/octopus.json --output output/demo.mp4 --width 360 --height 640 --fps 12`. Tam çalışma: `python studio_2d.py --fact 'Ahtapotların üç kalbi vardır'` (Gemini anahtarı ve ağ gerekir). Gemini Search grounding, metin ve Edge TTS için bağlantı/kota gerekir; tamamen bedelsiz çalışma garanti değildir. YouTube ayarları ana README'deki gibidir.

Bu dalda yeni 2D motor, Drive'daki `kahve_molasi.py` dosyasının eksiksiz kaynak kodu çalışma alanına indirilemediği için onun kodunu içe aktarmak yerine Pillow/FFmpeg yaklaşımı temel alınarak ayrı yazılmıştır. Orijinal dosya Drive'da değişmeden durmaktadır. Orijinal yardımcı fonksiyonların doğrudan ayrıştırılması sonraki adımdır.
