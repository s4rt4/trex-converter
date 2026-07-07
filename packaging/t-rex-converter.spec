# RPM packaging for the GTK4 front-end. Build with packaging/build-rpm.sh,
# which supplies the app_version macro from app/__init__.py and the source
# tarball via git archive.
%{!?app_version: %define app_version 0.0.0}

Name:           t-rex-converter
Version:        %{app_version}
Release:        1%{?dist}
Summary:        Convert media, images, documents, and PDFs locally
License:        MIT
URL:            https://github.com/s4rt4/trex-converter
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       python3 >= 3.11
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita >= 1.6
Requires:       python3-psutil
Requires:       python3-pymupdf
Requires:       hicolor-icon-theme

# Conversion engines — every feature degrades gracefully when its engine
# is missing (the dashboard shows what's installed), so these are
# recommendations, not hard requirements. ffmpeg intentionally isn't
# listed: Fedora ships ffmpeg-free while RPM Fusion ships ffmpeg, and
# naming either would fight the user's choice.
Recommends:     ImageMagick
Recommends:     qpdf
Recommends:     tesseract
Recommends:     pandoc
Recommends:     qrencode
Recommends:     zbar
Recommends:     libreoffice
Recommends:     inkscape
Recommends:     potrace
Recommends:     perl-Image-ExifTool

%description
T-Rex Converter is a native GTK4/libadwaita app that converts images,
video, audio, documents, PDFs, subtitles, ebooks, and archives locally —
a single front-end over best-in-class command-line engines (FFmpeg,
ImageMagick, LibreOffice, Pandoc, Tesseract, PyMuPDF/qpdf, and more),
with a task queue, presets, and bilingual built-in help.

%prep
%autosetup

%build
# Pure Python + assets; nothing to compile.

%install
mkdir -p %{buildroot}%{_datadir}/%{name}
cp -r app assets %{buildroot}%{_datadir}/%{name}/
# The GTK build ships only what it runs: drop the legacy Qt UI and its
# entry point (they need PySide6, which this package deliberately lacks).
rm -rf %{buildroot}%{_datadir}/%{name}/app/ui
rm -f %{buildroot}%{_datadir}/%{name}/app/main.py
find %{buildroot}%{_datadir}/%{name} -type d -name '__pycache__' -exec rm -rf {} +

install -Dm755 packaging/t-rex-converter.bin %{buildroot}%{_bindir}/%{name}
install -Dm644 packaging/io.github.s4rt4.trexconverter.desktop \
    %{buildroot}%{_datadir}/applications/io.github.s4rt4.trexconverter.desktop
install -Dm644 assets/icons/hicolor/scalable/apps/io.github.s4rt4.trexconverter.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/io.github.s4rt4.trexconverter.svg
for size in 16x16 32x32 48x48 64x64 128x128 256x256; do
    if [ -f "assets/icons/hicolor/$size/apps/t-rex-converter.png" ]; then
        install -Dm644 "assets/icons/hicolor/$size/apps/t-rex-converter.png" \
            "%{buildroot}%{_datadir}/icons/hicolor/$size/apps/io.github.s4rt4.trexconverter.png"
    fi
done

%files
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{_datadir}/applications/io.github.s4rt4.trexconverter.desktop
%{_datadir}/icons/hicolor/*/apps/io.github.s4rt4.trexconverter.*

%changelog
* Tue Jul 07 2026 s4rt4 <vinvan83@gmail.com> - 2.0.0-1
- GTK4/libadwaita rewrite: new shell, 26 converter pages, dashboard with
  quick convert and history, live-progress queue, bilingual help
- Reliability: queue-startup, cancel-race, preset round-trip, and Pango
  markup fixes; per-engine output-directory creation
