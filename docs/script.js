/* T-Rex Converter docs site. No dependencies, no tracking.
   Default language: English; Indonesian via the EN|ID toggle.
   Theme: light/dark, follows the OS by default, persisted on toggle. */
(function () {
  'use strict';
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── i18n ─────────────────────────────────────────────────────── */
  /* English lives in the markup; this map holds the Indonesian HTML. */
  var ID = {
    'nav.features': 'Fitur',
    'nav.try': 'Coba',
    'nav.pipeline': 'Alur tugas',
    'nav.built': 'Teknologi',
    'hero.tagline': 'Konversi apa saja. Tanpa unggah apa pun.',
    'hero.lede': 'Aplikasi native <strong>GTK4 / libadwaita</strong> untuk Linux yang mengonversi gambar, video, audio, dokumen, PDF, subtitle, ebook, dan arsip — sepenuhnya di mesin Anda. Satu antarmuka tenang di atas FFmpeg, ImageMagick, LibreOffice, Pandoc, Tesseract, dan kawan-kawan.',
    'hero.download': 'Unduh .rpm (2.0.0)',
    'hero.install': 'Cara memasang',
    'hero.github': 'Lihat di GitHub',
    'hero.note': '.rpm untuk Fedora 41+ (noarch). Semua versi ada di <a href="https://github.com/s4rt4/trex-converter/releases">halaman rilis</a>.',
    'hero.badge3': 'Asli Linux',
    'hero.badge4': '100% lokal',
    'show.invite': 'Aplikasinya mengikuti suasana terang atau gelap Anda — dan <em>halaman ini juga</em>:',
    'theme.light': 'Terang',
    'theme.dark': 'Gelap',
    'show.note': 'Dashboard sungguhan: jatuhkan file ke kartu dan ia terbuka otomatis di konverter yang tepat.',
    'stat.converters': 'tujuan konversi di sidebar',
    'stat.tests': 'tes otomatis',
    'stat.engines': 'engine command-line yang dirangkai',
    'stat.uploads': 'file terunggah, selamanya',
    'philo.title': 'Dua belas alat tajam, satu antarmuka tenang',
    'philo.body': 'T-Rex tidak menulis ulang proses konversi. Ia merangkai engine terbaik di kelasnya — FFmpeg, ImageMagick, LibreOffice, Pandoc, Tesseract, PyMuPDF/qpdf, dan lainnya — di balik satu antarmuka GTK4/libadwaita: antrean tugas async, preset, dan dashboard, alih-alih selusin man page. Semua engine opsional; fiturnya menyala saat engine-nya terpasang.',
    'feat.title': 'Semua yang bisa terjadi pada sebuah file',
    'feat.hint': 'Klik kartu untuk detailnya.',
    'f1.t': 'Gambar',
    'f1.p': 'Apa pun↔apa pun: png, jpg, webp, avif, heic, gif, tiff, bmp, ico.',
    'f1.more': '<ul><li>Resize, crop, warna, filter, border, watermark</li><li>Buang metadata saat ekspor</li><li>Montage: susun banyak gambar jadi satu grid</li><li>Render SVG ke bitmap &amp; trace bitmap ke vektor</li></ul>',
    'f2.t': 'Video',
    'f2.p': 'mp4, mkv, webm, mov — lengkap dengan senjata FFmpeg.',
    'f2.more': '<ul><li>Trim, transform, kompresi via CRF atau target ukuran</li><li>Overlay watermark/logo, burn-in subtitle</li><li>GIF &amp; WebP animasi, lembar thumbnail</li><li>Gabung (concat) banyak klip; ekstrak trek audionya</li></ul>',
    'f3.t': 'Audio',
    'f3.p': 'mp3, wav, flac, m4a, opus, ogg — plus perbaikan yang benar-benar Anda butuhkan.',
    'f3.more': '<ul><li>Trim &amp; fade in/out</li><li>Normalisasi loudness (EBU R128)</li><li>Hapus vokal, edit tag ID3</li><li>Mix banyak trek menjadi satu file</li></ul>',
    'f4.t': 'Dokumen &amp; ebook',
    'f4.p': 'Matriks LibreOffice: dokumen, sheet, dan slide keluar-masuk semua format office.',
    'f4.more': '<ul><li>docx / odt / xlsx / pptx / pdf / html / epub…</li><li>Ekspor PDF/A dan PDF berkata sandi</li><li>Slide jadi gambar; gabungkan dokumen jadi satu PDF</li><li>Ebook &amp; markup via Pandoc</li></ul>',
    'f5.t': 'Perkakas PDF',
    'f5.p': 'Sembilan halaman khusus PDF — dari konversi sampai pembandingan forensik.',
    'f5.more': '<ul><li>Konversi ke png / jpg / txt / html / docx / epub</li><li>Ekstrak, susun ulang, putar halaman; pisah &amp; gabung</li><li>Kompres, enkripsi/dekripsi, watermark, redaksi</li><li>Penomoran halaman, compare, ekstrak gambar &amp; lampiran</li></ul>',
    'f6.t': 'OCR, QR &amp; utilitas',
    'f6.p': 'Dari kertas jadi PDF yang bisa dicari — plus pekerjaan kecil khas meja kerja.',
    'f6.more': '<ul><li>OCR ke PDF yang bisa dicari, txt, atau hOCR (Tesseract)</li><li>QR &amp; barcode: buat dan baca</li><li>Arsip: ekstrak dan kompres</li><li>Metadata media: baca, buang, edit (ExifTool)</li></ul>',
    'f7.t': 'Dashboard sebagai beranda',
    'f7.p': 'Jatuhkan file apa pun ke kartu quick-convert; ia terbuka otomatis di konverter yang tepat.',
    'f7.more': '<ul><li>Chip pintasan ke tiap keluarga konverter</li><li>Grafik aktivitas &amp; riwayat tugas dengan tombol buka-folder</li><li>Panel ketersediaan engine langsung, indikator CPU/RAM</li><li>Bantuan bawaan dalam bahasa Inggris &amp; Indonesia</li></ul>',
    'f8.t': 'Antrean tugas',
    'f8.p': 'Konversi berjalan sebagai tugas async — UI tidak pernah membeku.',
    'f8.more': '<ul><li>Progres langsung, batalkan &amp; ulangi per tugas</li><li>Detail per tugas dengan log lengkap engine-nya</li><li>Tugas tertunda dilanjutkan setelah restart</li><li>Preset per halaman, tema terang/gelap tersimpan</li><li><a href="#try">Lihat demo antreannya di bawah</a></li></ul>',
    'try.title': 'Tidak perlu memasang untuk bagian ini',
    'try.lede': 'Dua demo kecil, langsung di halaman ini.',
    'demo1.title': 'Quick convert, seperti di dashboard',
    'demo1.hint': 'Pilih sebuah file — lihat ia mendarat di konverter yang tepat:',
    'demo1.dzidle': 'Jatuhkan file apa pun di sini — atau klik chip di atas',
    'demo1.dzsub': 'Otomatis terbuka di konverter yang tepat',
    'demo2.title': 'Antrean tugas',
    'demo2.btn': 'Tambah tugas',
    'demo2.running': 'Berjalan',
    'demo2.done': 'Selesai',
    'pipe.title': 'Hidup sebuah tugas — seluruhnya di mesin Anda',
    'pipe.body': 'Tanpa akun, tanpa kredit cloud, tanpa "diproses di server kami". Konversi adalah pipeline lokal dari jatuh sampai jadi. Telusuri langkahnya:',
    'pipe.s1': 'Jatuhkan',
    'pipe.s2': 'Deteksi',
    'pipe.s3': 'Konversi',
    'pipe.s4': 'Selesai',
    'built.title': 'Di balik kapnya',
    'built.lede': 'Tiap keluarga media mendapat engine yang paling jago di bidangnya.',
    'l1': 'Video &amp; audio: konversi, trim, kompres, concat, mix, GIF',
    'l2': 'Konversi gambar, operasi, dan montage',
    'l3': 'Matriks dokumen — docx/odt/xlsx/pptx/pdf dan lainnya, headless',
    'l4': 'Perkakas PDF: render, susun ulang, enkripsi, compare',
    'l5': 'OCR ke PDF yang bisa dicari, txt, dan hOCR',
    'l6': 'Konversi ebook &amp; markup',
    'l7': 'Render SVG &amp; trace bitmap-ke-vektor',
    'l8': 'QR &amp; barcode: buat dan baca',
    'l9': 'Metadata media: baca, buang, edit',
    'l10': 'Cangkang aplikasi native, berlisensi MIT',
    'built.note': 'Semua engine adalah dependensi <em>lunak</em>: aplikasi tetap jalan tanpanya, fitur terkait mati dengan anggun, dan panel Engines di Dashboard menunjukkan ketersediaannya secara langsung.',
    'inst.title': 'Memasang di Fedora',
    'inst.s1': 'Ambil RPM dari rilis terbaru &amp; pasang',
    'inst.s2': 'Tambahkan FFmpeg untuk video &amp; audio (pilih satu)',
    'inst.s3': 'Opsional: paket engine selebihnya',
    'inst.opt': 'Mau jalan dari source? <code>git clone</code> repo-nya lalu <code>./run-gtk.sh</code> — lihat prasyarat GTK4-nya di <a href="https://github.com/s4rt4/trex-converter#run-from-source">README</a>.',
    'close.title': 'Perangkat lunak bebas. File Anda tidak pernah meninggalkan rumah.',
    'close.src': 'Sumber di GitHub',
    'foot.main': 'T-Rex Converter, berlisensi <a href="https://github.com/s4rt4/trex-converter/blob/gtk4/packaging/debian/copyright">MIT</a>. Dibuat untuk Linux.',
    'foot.credit': 'Semua kredit konversi milik para engine: FFmpeg, ImageMagick, LibreOffice, Pandoc, Tesseract, PyMuPDF, qpdf, Inkscape, potrace, qrencode, zbar, dan ExifTool.'
  };

  var TITLES = {
    en: 'T-Rex Converter — Convert anything. Upload nothing.',
    id: 'T-Rex Converter — Konversi apa saja. Tanpa unggah apa pun.'
  };

  /* Strings rendered by JS, per language */
  var DZ = {
    en: {
      hit: '{file} → the <span class="conv">{conv}</span> converter opens',
      hitsub: 'Detected automatically — ready to become:'
    },
    id: {
      hit: '{file} → terbuka di konverter <span class="conv">{conv}</span>',
      hitsub: 'Terdeteksi otomatis — siap menjadi:'
    }
  };
  var PIPE_STEPS = {
    en: [
      'Drop any file on the dashboard’s quick-convert card — or straight onto a converter page. The file type decides where it goes.',
      'The registry maps the file to the right one of 26 converters and opens it with sensible defaults. Presets fill in the rest.',
      'The conversion runs as an async task: live progress, cancel and retry, and the engine’s full log kept per task. Quit halfway? Pending tasks resume on the next start.',
      'The result lands where you chose, history keeps an open-folder button, and the activity chart ticks up. Nothing was uploaded — there is nowhere to upload to.'
    ],
    id: [
      'Jatuhkan file apa pun ke kartu quick-convert di dashboard — atau langsung ke halaman konverternya. Jenis file menentukan tujuannya.',
      'Registry memetakan file ke satu dari 26 konverter yang tepat dan membukanya dengan default yang masuk akal. Preset mengisi sisanya.',
      'Konversi berjalan sebagai tugas async: progres langsung, batalkan dan ulangi, plus log lengkap engine tersimpan per tugas. Keluar di tengah jalan? Tugas tertunda dilanjutkan saat aplikasi dibuka lagi.',
      'Hasilnya mendarat di tempat pilihan Anda, riwayat menyimpan tombol buka-folder, dan grafik aktivitas bertambah. Tidak ada yang terunggah — memang tidak ada tempat mengunggahnya.'
    ]
  };

  var lang = 'en';
  var enCache = {};   // English innerHTML (from the markup), filled at init

  document.querySelectorAll('[data-i18n]').forEach(function (el) {
    var key = el.getAttribute('data-i18n');
    if (!(key in enCache)) enCache[key] = el.innerHTML;
  });

  function setLang(next) {
    lang = next === 'id' ? 'id' : 'en';
    document.documentElement.lang = lang;
    document.title = TITLES[lang];
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      var html = lang === 'id' ? ID[key] : enCache[key];
      if (html != null) el.innerHTML = html;
    });
    document.querySelectorAll('.lang-toggle button').forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-lang') === lang);
    });
    renderDrop();          // re-render the quick-convert demo state
    setPipe(pipeCurrent);  // re-render the pipeline detail
    try { localStorage.setItem('trex-lang', lang); } catch (e) { /* private mode */ }
  }

  document.querySelectorAll('.lang-toggle button').forEach(function (b) {
    b.addEventListener('click', function () { setLang(b.getAttribute('data-lang')); });
  });

  /* ── Theme (page + screenshot, synced) ────────────────────────── */
  function setTheme(t, persist) {
    t = t === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', t);
    document.querySelectorAll('[data-theme-pick]').forEach(function (c) {
      c.classList.toggle('active', c.getAttribute('data-theme-pick') === t);
    });
    if (persist) {
      try { localStorage.setItem('trex-theme', t); } catch (e) { /* private mode */ }
    }
  }
  document.querySelectorAll('[data-theme-pick]').forEach(function (c) {
    c.addEventListener('click', function () {
      setTheme(c.getAttribute('data-theme-pick'), true);
    });
  });
  document.getElementById('modeBtn').addEventListener('click', function () {
    var cur = document.documentElement.getAttribute('data-theme');
    setTheme(cur === 'dark' ? 'light' : 'dark', true);
  });
  (function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem('trex-theme'); } catch (e) { /* private mode */ }
    if (saved === 'light' || saved === 'dark') { setTheme(saved, false); return; }
    setTheme(window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light', false);
  })();

  /* ── Scroll reveal ────────────────────────────────────────────── */
  var revealEls = document.querySelectorAll('.reveal');
  if (!reduced && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  /* ── Stat counters ────────────────────────────────────────────── */
  function runCount(el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    if (reduced || target === 0) { el.textContent = target; return; }
    var t0 = performance.now(), dur = 1100;
    function tick(now) {
      var p = Math.min(1, (now - t0) / dur);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  var nums = document.querySelectorAll('.stat-num');
  if ('IntersectionObserver' in window) {
    var ioNum = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { runCount(e.target); ioNum.unobserve(e.target); }
      });
    }, { threshold: 0.6 });
    nums.forEach(function (el) { ioNum.observe(el); });
  } else {
    nums.forEach(runCount);
  }

  /* ── Expandable feature cards ─────────────────────────────────── */
  document.querySelectorAll('.card-head').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var card = btn.closest('.card');
      var open = card.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });

  /* ── Demo 1: quick convert ────────────────────────────────────── */
  var FILES = [
    { name: 'photo.heic',  icon: 'i-image', conv: 'Image',     targets: ['png', 'jpg', 'webp', 'avif'] },
    { name: 'clip.mov',    icon: 'i-film',  conv: 'Video',     targets: ['mp4', 'mkv', 'webm', 'gif'] },
    { name: 'voice.m4a',   icon: 'i-music', conv: 'Audio',     targets: ['mp3', 'flac', 'opus', 'ogg'] },
    { name: 'slides.pptx', icon: 'i-doc',   conv: 'Document',  targets: ['pdf', 'odp', 'html', 'png'] },
    { name: 'scan.pdf',    icon: 'i-file',  conv: 'PDF tools', targets: ['png', 'docx', 'txt', 'epub'] }
  ];
  var chipsWrap = document.getElementById('fileChips');
  var dropZone = document.getElementById('dropZone');
  var dzTitle = document.getElementById('dzTitle');
  var dzSub = document.getElementById('dzSub');
  var dzTargets = document.getElementById('dzTargets');
  var picked = null;   // index into FILES, or null when idle

  FILES.forEach(function (f, i) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'fchip';
    b.innerHTML = '<svg class="ic"><use href="#' + f.icon + '"/></svg> ' + f.name;
    b.addEventListener('click', function () { pickFile(i); });
    chipsWrap.appendChild(b);
  });

  function renderDrop() {
    var chips = chipsWrap.querySelectorAll('.fchip');
    chips.forEach(function (c, i) { c.classList.toggle('active', i === picked); });
    if (picked == null) {
      dzTitle.innerHTML = lang === 'id' ? ID['demo1.dzidle'] : enCache['demo1.dzidle'];
      dzSub.innerHTML = lang === 'id' ? ID['demo1.dzsub'] : enCache['demo1.dzsub'];
      dzTargets.innerHTML = '';
      return;
    }
    var f = FILES[picked];
    dzTitle.innerHTML = DZ[lang].hit.replace('{file}', f.name).replace('{conv}', f.conv);
    dzSub.innerHTML = DZ[lang].hitsub;
    dzTargets.innerHTML = '';
    f.targets.forEach(function (t, i) {
      var s = document.createElement('span');
      s.className = 'tchip';
      s.textContent = '.' + t;
      s.style.animationDelay = reduced ? '0s' : (i * 0.09) + 's';
      dzTargets.appendChild(s);
    });
  }
  function pickFile(i) {
    picked = i;
    dropZone.classList.remove('hit');
    void dropZone.offsetWidth;   // restart the pulse animation
    dropZone.classList.add('hit');
    renderDrop();
  }

  /* ── Demo 2: task queue ───────────────────────────────────────── */
  var POOL = [
    { name: 'holiday.heic → webp',        engine: 'ImageMagick', icon: 'i-image' },
    { name: 'lecture.mov → mp4',          engine: 'FFmpeg',      icon: 'i-film' },
    { name: 'draft.docx → pdf',           engine: 'LibreOffice', icon: 'i-doc' },
    { name: 'scan.pdf → searchable pdf',  engine: 'Tesseract',   icon: 'i-scan' },
    { name: 'podcast.wav → opus',         engine: 'FFmpeg',      icon: 'i-music' },
    { name: 'notes.md → epub',            engine: 'Pandoc',      icon: 'i-layers' },
    { name: 'photos → montage.png',       engine: 'ImageMagick', icon: 'i-image' }
  ];
  var qList = document.getElementById('qList');
  var qRunning = document.getElementById('qRunning');
  var qDone = document.getElementById('qDone');
  var addBtn = document.getElementById('addTaskBtn');
  var poolIdx = 0, running = 0, completed = 0;

  function refreshTiles() {
    qRunning.textContent = running;
    qDone.textContent = completed;
  }
  function trimList() {
    while (qList.children.length > 5) {
      var oldest = qList.querySelector('.q-item.done');
      if (!oldest) break;
      qList.removeChild(oldest);
    }
  }
  function addTask() {
    var t = POOL[poolIdx++ % POOL.length];
    var item = document.createElement('div');
    item.className = 'q-item';
    item.innerHTML =
      '<div class="q-row">' +
        '<svg class="ic"><use href="#' + t.icon + '"/></svg>' +
        '<span class="q-name">' + t.name + '</span>' +
        '<svg class="ic q-check"><use href="#i-check"/></svg>' +
        '<span class="q-engine">' + t.engine + '</span>' +
      '</div>' +
      '<div class="q-track"><div class="q-fill"></div></div>';
    qList.appendChild(item);
    trimList();
    running++;
    refreshTiles();

    var fill = item.querySelector('.q-fill');
    var dur = 2200 + Math.random() * 2200;
    var t0 = performance.now();
    function finish() {
      item.classList.add('done');
      running--;
      completed++;
      refreshTiles();
    }
    if (reduced) { fill.style.width = '100%'; setTimeout(finish, 400); return; }
    function tick(now) {
      var p = Math.min(1, (now - t0) / dur);
      fill.style.width = (100 * (1 - Math.pow(1 - p, 2))) + '%';
      if (p < 1) requestAnimationFrame(tick);
      else finish();
    }
    requestAnimationFrame(tick);
  }
  addBtn.addEventListener('click', addTask);

  /* Seed the queue when it scrolls into view */
  var qSeeded = false;
  function seedQueue() {
    if (qSeeded) return;
    qSeeded = true;
    addTask();
    setTimeout(addTask, reduced ? 600 : 900);
    setTimeout(addTask, reduced ? 1200 : 2100);
  }
  if ('IntersectionObserver' in window) {
    var ioQ = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { seedQueue(); ioQ.unobserve(e.target); }
      });
    }, { threshold: 0.3 });
    ioQ.observe(qList);
  } else {
    seedQueue();
  }

  /* ── Pipeline stepper ─────────────────────────────────────────── */
  var stepBtns = Array.prototype.slice.call(document.querySelectorAll('.step'));
  var pipeDetail = document.getElementById('pipeDetail');
  var pipeBar = document.getElementById('pipeBar');
  var pipeCurrent = 0;
  function setPipe(i) {
    pipeCurrent = i;
    stepBtns.forEach(function (b, j) { b.classList.toggle('active', i === j); });
    pipeDetail.textContent = PIPE_STEPS[lang][i];
    pipeBar.style.width = ((i + 1) / stepBtns.length * 100) + '%';
  }
  var pipeAuto = null;
  if (!reduced) {
    pipeAuto = setInterval(function () {
      setPipe((pipeCurrent + 1) % stepBtns.length);
    }, 4200);
  }
  stepBtns.forEach(function (b, i) {
    b.addEventListener('click', function () {
      if (pipeAuto) { clearInterval(pipeAuto); pipeAuto = null; }
      setPipe(i);
    });
  });
  setPipe(0);

  /* ── Init language (default en; honor the saved choice) ───────── */
  var savedLang = null;
  try { savedLang = localStorage.getItem('trex-lang'); } catch (e) { /* private mode */ }
  setLang(savedLang === 'id' ? 'id' : 'en');
})();
