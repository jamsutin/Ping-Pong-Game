"""Tes runtime browser nyata untuk hasil build Pygbag (Chromium + Playwright).

Pemakaian:
    python tests/browser_smoke_test.py build/web
    python tests/browser_smoke_test.py https://jamsutin.github.io/Ping-Pong-Game/

Membuka build/web lewat server lokal, menunggu runtime Python (WASM) memuat,
lalu MEMBUKTIKAN:
  1. semua checkpoint "[BOOT] ..." muncul di Console sampai "First frame drawn"
  2. tidak ada "[BOOT][ERROR]", traceback, atau uncaught page error
  3. canvas benar-benar berisi gambar (bukan layar polos abu-abu/cokelat)
  4. ENTER memulai permainan dan ESC mem-pause (tampilan canvas berubah)

Opsional PP_CDN_MIRROR=<folder>: layani CDN pygame-web dari salinan lokal
(struktur repo pygame-web/archives) untuk lingkungan tanpa akses internet.
"""
import functools
import hashlib
import http.server
import mimetypes
import os
import pathlib
import re
import sys
import threading
import time

from playwright.sync_api import sync_playwright

REQUIRED = [
    "[BOOT] main.py imported",
    "[BOOT] pygame imported",
    "[BOOT] Game module imported",
    "[BOOT] Pygame display initialized",
    "[BOOT] Fonts initialized",
    "[BOOT] Game object created",
    "[BOOT] First frame drawn",
    "[BOOT] Game loop running",
]
TIMEOUT_S = int(os.environ.get("PP_TIMEOUT", "180"))


def canvas_signature(page):
    """Hash + jumlah warna unik dari piksel canvas game (di-sampel)."""
    data = page.evaluate(
        """() => {
          const c = document.querySelector('canvas#canvas') || document.querySelector('canvas');
          if (!c) return null;
          const t = document.createElement('canvas'); t.width = 160; t.height = 100;
          const x = t.getContext('2d'); x.drawImage(c, 0, 0, 160, 100);
          return Array.from(x.getImageData(0, 0, 160, 100).data);
        }"""
    )
    if not data:
        return None, 0
    px = [tuple(data[i:i + 3]) for i in range(0, len(data), 4)]
    return hashlib.md5(bytes(data)).hexdigest(), len({(r // 8, g // 8, b // 8) for r, g, b in px})


def main(build_dir):
    mirror = os.environ.get("PP_CDN_MIRROR")
    srv = None
    if build_dir.startswith(("http://", "https://")):
        url = build_dir  # uji situs yang sudah di-deploy (mis. GitHub Pages)
    else:
        build = pathlib.Path(build_dir).resolve()
        assert (build / "index.html").is_file(), f"{build}/index.html tidak ada"
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(build))
        handler.log_message = lambda *a, **k: None
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"

    logs, errors = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                           "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = browser.new_context(viewport={"width": 1280, "height": 800}).new_page()
        t0 = time.time()
        page.on("console", lambda m: logs.append(m.text))
        page.on("pageerror", lambda e: errors.append(str(e)))

        if mirror:
            root = pathlib.Path(mirror)

            def serve_mirror(route):
                p = re.sub(r"/+", "/", route.request.url.split("pygame-web.github.io/", 1)[1]).split("?")[0]
                m = re.match(r"cdn/0\.9\.\d+/(.*)", p)
                if m:
                    f = "cpythonrc.py" if m.group(1) == "pythonrc.py" else m.group(1)
                    path = root / "0.9" / f
                else:
                    path = root / re.sub(r"^archives/", "", p)
                if path.is_file():
                    ct = "application/wasm" if path.suffix == ".wasm" else (mimetypes.guess_type(path.name)[0] or "application/octet-stream")
                    route.fulfill(status=200, body=path.read_bytes(),
                                  headers={"content-type": ct, "access-control-allow-origin": "*"})
                else:
                    route.fulfill(status=404, body="not found")

            page.route("https://pygame-web.github.io/**", serve_mirror)

        page.goto(url, wait_until="domcontentloaded")

        # 1) tunggu semua checkpoint BOOT
        deadline = time.time() + TIMEOUT_S
        while time.time() < deadline:
            joined = "\n".join(logs)
            if "[BOOT][ERROR]" in joined or errors or "Traceback (most recent call last)" in joined:
                break
            if all(c in joined for c in REQUIRED):
                break
            page.wait_for_timeout(500)
        joined = "\n".join(logs)
        failed = False
        for c in REQUIRED:
            ok = c in joined
            print(("PASS " if ok else "FAIL ") + c)
            failed |= not ok

        # 2) tidak ada error
        bad = [l for l in logs if "[BOOT][ERROR]" in l or "Traceback (most recent call last)" in l]
        for l in bad + errors:
            print("ERROR:", l[:2000])
        failed |= bool(bad or errors)
        print(("FAIL" if bad or errors else "PASS") + " tidak ada exception di Console")

        if not failed:
            # 3) canvas berisi gambar menu
            page.wait_for_timeout(1500)
            sig_menu, colors = canvas_signature(page)
            ok = sig_menu is not None and colors >= 12
            print(("PASS" if ok else "FAIL") + f" canvas berisi gambar (warna unik: {colors})")
            failed |= not ok

            # 4) input keyboard: ENTER -> main, ESC -> pause
            page.click("canvas")
            page.keyboard.press("Enter")
            page.wait_for_timeout(2500)
            sig_play, _ = canvas_signature(page)
            ok = sig_play != sig_menu
            print(("PASS" if ok else "FAIL") + " ENTER memulai permainan (canvas berubah)")
            failed |= not ok
            page.wait_for_timeout(5000)
            page.keyboard.press("Escape")
            page.wait_for_timeout(1500)
            sig_pause1, _ = canvas_signature(page)
            page.wait_for_timeout(1500)
            sig_pause2, _ = canvas_signature(page)
            page.keyboard.press("Escape")
            page.wait_for_timeout(1500)
            sig_resume, _ = canvas_signature(page)
            ok = sig_pause1 not in (None, sig_resume)
            print(("PASS" if ok else "FAIL") + " ESC mem-pause lalu melanjutkan permainan")
            failed |= not ok
            if os.environ.get("PP_SCREENSHOT"):
                page.screenshot(path=os.environ["PP_SCREENSHOT"])
        print(f"selesai dalam {time.time() - t0:.0f} detik")
        browser.close()
    if srv:
        srv.shutdown()
    if failed:
        print("\n--- Console terakhir ---\n" + "\n".join(logs[-40:]))
        sys.exit(1)
    print("SEMUA TES BROWSER LULUS")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/web")
