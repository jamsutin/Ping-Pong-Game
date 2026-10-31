"""Entrypoint browser untuk Pygbag.

Versi desktop tetap dijalankan melalui:
    python ping_pong_cinematic.py

Pygbag membutuhkan main.py dan game loop asynchronous.
"""
import asyncio
import traceback
import platform

# Kirim diagnostik Python ke Console browser. print() Pygbag diarahkan ke
# terminal/REPL internal, bukan ke DevTools Console.
def web_log(message):
    try:
        platform.console.log("[PingPong Web] " + str(message))
    except Exception:
        print("[PingPong Web] " + str(message), flush=True)


web_log("main.py mulai dimuat")

try:
    import pygame
    web_log("pygame berhasil di-import")

    import ping_pong_cinematic as game
    web_log("ping_pong_cinematic berhasil di-import")
except Exception:
    web_log("GAGAL saat import modul game:")
    web_log(traceback.format_exc())
    raise

# Audio sintetis tetap tersedia pada desktop, tetapi tidak digunakan di browser.
# Inisialisasi mixer SDL di browser dapat macet pada SDL_OpenAudioDevice
# sebelum frame pertama tampil.
game.WEB_MODE = True


async def main():
    try:
        web_log("inisialisasi display/font/event")
        # Jangan panggil pygame.init() di browser: fungsi itu menginisialisasi
        # seluruh subsistem, termasuk mixer/audio. Game web hanya butuh modul ini.
        pygame.display.init()
        pygame.font.init()
        pygame.event.init()
        web_log("display, font, event siap")

        app = game.Game()
        app._web_running = True

        # sys.exit() sesuai untuk aplikasi desktop, tetapi tidak diperlukan
        # untuk menghentikan loop aplikasi yang berjalan di browser.
        def stop_web_game():
            app._web_running = False

        app.quit = stop_web_game
        web_log("objek Game berhasil dibuat; mulai game loop")

        while app._web_running:
            app.handle_events()
            if not app._web_running:
                break
            app.update()
            app.draw()
            pygame.display.flip()
            app.clock.tick(game.FPS)

            # Wajib untuk memberi kendali kembali ke event loop browser.
            await asyncio.sleep(0)

    except Exception:
        web_log("ERROR saat game berjalan:")
        web_log(traceback.format_exc())
        raise


asyncio.run(main())
