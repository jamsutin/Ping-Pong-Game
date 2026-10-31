"""Entrypoint browser untuk Pygbag.

Versi desktop tetap dijalankan melalui:
    python ping_pong_cinematic.py

Pygbag membutuhkan main.py dan game loop asynchronous.
"""
import asyncio
import traceback

import pygame

import ping_pong_cinematic as game

# Audio sintetis tetap tersedia pada desktop, tetapi tidak digunakan di browser.
# Inisialisasi mixer SDL di browser dapat macet pada SDL_OpenAudioDevice
# sebelum frame pertama tampil.
game.WEB_MODE = True


async def main():
    print("[PingPong Web] main.py mulai dijalankan", flush=True)

    # Jangan panggil pygame.init() di browser: fungsi itu menginisialisasi
    # seluruh subsistem, termasuk mixer/audio. Game web hanya butuh modul ini.
    pygame.display.init()
    pygame.font.init()
    pygame.event.init()
    pygame.key.init()

    print("[PingPong Web] display, font, event siap", flush=True)

    try:
        app = game.Game()
        app._web_running = True

        # sys.exit() sesuai untuk aplikasi desktop, tetapi tidak diperlukan
        # untuk menghentikan loop aplikasi yang berjalan di browser.
        def stop_web_game():
            app._web_running = False

        app.quit = stop_web_game
        print("[PingPong Web] objek Game berhasil dibuat", flush=True)

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
        print("[PingPong Web] ERROR saat game berjalan:", flush=True)
        traceback.print_exc()
        raise


asyncio.run(main())
