"""Entrypoint browser untuk Pygbag.

Versi desktop tetap dijalankan melalui:
    python ping_pong_cinematic.py

Pygbag membutuhkan main.py dan game loop asynchronous.

Setiap tahap startup mengirim checkpoint "[BOOT] ..." ke Console browser
(DevTools). Tes otomatis di tests/browser_smoke_test.py membaca checkpoint ini
untuk membuktikan game benar-benar mencapai frame pertama.
"""
import asyncio
import platform
import traceback


def web_log(message):
    """Kirim pesan ke DevTools Console; print() Pygbag hanya ke terminal internal."""
    try:
        platform.console.log(str(message))
    except Exception:
        print(str(message), flush=True)


def boot(message):
    web_log("[BOOT] " + message)


boot("main.py imported")

try:
    import pygame

    boot("pygame imported")

    import ping_pong_cinematic as game

    boot("Game module imported")
except Exception:
    web_log("[BOOT][ERROR] import gagal:\n" + traceback.format_exc())
    raise

# Audio sintetis tetap tersedia pada desktop, tetapi tidak dipakai di browser.
# Inisialisasi mixer SDL di browser dapat macet sebelum frame pertama tampil.
game.WEB_MODE = True


async def main():
    try:
        # Jangan panggil pygame.init(): itu ikut menyalakan mixer/audio.
        # (pygame.event tidak punya init(); ia aktif bersama display.)
        pygame.display.init()
        boot("Pygame display initialized")
        pygame.font.init()
        boot("Fonts initialized")

        app = game.Game()
        app._web_running = True
        boot("Game object created")

        # sys.exit() cocok untuk desktop, tetapi tidak untuk loop di browser.
        def stop_web_game():
            app._web_running = False

        app.quit = stop_web_game

        first_frame = True
        while app._web_running:
            app.handle_events()
            if not app._web_running:
                break
            app.update()
            app.draw()
            pygame.display.flip()
            if first_frame:
                first_frame = False
                boot("First frame drawn")
                boot("Game loop running")
            app.clock.tick(game.FPS)

            # Wajib: beri kendali kembali ke event loop browser.
            await asyncio.sleep(0)

    except Exception:
        web_log("[BOOT][ERROR] game berhenti:\n" + traceback.format_exc())
        raise


asyncio.run(main())
