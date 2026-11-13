# Molla — 15 saniyelik Türkçe bilgi Shorts'u

Gemini, genel kültür konusunu araştırır ve üç sahne planlar; Gemini görsel modeli sahne görselleri üretir; Pillow ve FFmpeg görselleri canlandırır; Edge TTS Türkçe erkek ses ve kelime zamanlaması üretir. Telifsiz dış müzik indirilmez: hafif arka plan melodisi ve geçiş sesleri programatik olarak üretilir. Sonuç 1080×1920, 30 fps, 15 saniyelik MP4'tür. AI video modeli yoktur: 3D görünümlü **sabit görseller** kamera hareketleriyle canlandırılır; karakter animasyonu veya dudak senkronu yapılmaz.

## İlk kurulum
1. GitHub → Settings → Secrets and variables → Actions → New repository secret: `GEMINI_API_KEY` ekle. API anahtarı [Google AI Studio](https://aistudio.google.com/) üzerinden alınır. Metin modeli, Google Search grounding ve görsel modeli için hesap erişimi/kota gerekir; ücretsiz kota garanti değildir ve modele/bölgeye göre değişir. Ücretsiz kotan yoksa çağrılar ücretli olabilir veya başarısız olur. Harcama ve kota ayarlarını kontrol et.
2. Google Cloud'da YouTube Data API v3 etkinleştir; OAuth consent ekranını ve **Desktop app** OAuth istemcisini oluştur. Testing modundaysa kendi Google hesabını test kullanıcılarına ekle. İstemci JSON'unu **kendi cihazına** indir, repoya yükleme.
3. Kendi bilgisayarında `pip install google-auth-oauthlib` sonra `python get_youtube_token.py client_secret.json` çalıştır; kanal sahibi hesapla izin ver. Çıktıdaki `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` değerlerini GitHub Actions secrets'a ekle. Testing modundaki OAuth yetkileri süreli olabilir ve yenilemek gerekebilir.
4. Actions → **15 saniyelik Shorts üret** → Run workflow. İsteğe bağlı bilgi gir; boşsa sistem konu seçer. `publish` kapatılırsa YouTube yüklemeden yalnızca artifact üretilir. Zamanlı üretim varsayılan her gün 12:00 İstanbul'dur (09:00 UTC), GitHub geciktirebilir.

## Çıktı
Workflow artifact: `shorts.mp4`, `plan.json`, `sources.json`, `captions.srt`. Yükleme başarılıysa `yukleme-*` artifact'ında video ID'si vardır. YouTube videoları **private** yüklenir; yayına almak sana kalır. YouTube doğrulanmamış API projelerine ek sınırlamalar uygulayabilir. Altyazı sesin kelime sınırlarından oluşturulur ve görüntüye gömülür. Artifact'lar 14 gün tutulur.

## Sınırlamalar
- Gemini Search kaynak sağlamazsa otomatik üretim durur; kaynaklar bulunması olgunun doğru olduğunu garanti etmez. Yayın öncesi incele. Kullanıcı girdisi de grounding ile kontrol edilmeye çalışılır.
- Tekrarları azaltmak için başarılı yüklemelerin başlıkları `history.json` içinde tutulur; tekrarsızlık garanti değildir. Manuel sadece render modu geçmişe yazmaz. Başarılı upload sonrası history commit'i başarısız olursa ikinci çalıştırma tekrar video yükleyebilir.
- TTS (Edge TTS, Microsoft servisi) ağ ve hizmet erişimi ister; resmi ücretsiz kullanım kotası veya süreklilik garantisi yoktur. Görsel modeli tek istekte 3 görsel üretir; tutarlı karakter garantisi yoktur. Model hız/kota/ücret limitleri geçerlidir.
- YouTube yüklemesinde ağ kesintisi sonucu belirsizse tekrar çalıştırmadan önce kanalını kontrol et; tekrar yükleme mümkün.
- Model seçimi: `TEXT_MODEL` ve `IMAGE_MODEL` ortam değişkenleri. Varsayılan `gemini-2.5-flash` ve `gemini-2.5-flash-image`. Erişim ve ücretleri kontrol et.
- Workflow bağımlılıkları ve dış API'ler değişebilir. Gerçek Gemini ve YouTube kimlik bilgileri olmadan canlı entegrasyon doğrulanamaz.

## Yerelde çalıştırma
`pip install -r requirements.txt`, `GEMINI_API_KEY` ortam değişkenini ayarla, FFmpeg ve DejaVu Sans kur; `python studio.py --fact "Ahtapotların üç kalbi vardır"`. Varsayılan çıktı `output/shorts.mp4`.
