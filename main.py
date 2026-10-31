"""Entrypoint browser untuk Pygbag.

Versi desktop tetap dijalankan melalui:
    python ping_pong_cinematic.py

Pygbag membutuhkan main.py dan game loop asynchronous.
"""
import asyncio

import pygame

import ping_pong_cinematic as game

# Browser tidak memerlukan audio sintetis; menyiapkannya saat startup
# dapat memblokir event loop WebAssembly cukup lama.
game.WEB_MODE = True


async def main():
    pygame.mixer.pre_init(game.SAMPLE_RATE, -16, 1, 512)
    pygame.init()

    app = game.Game()
    app._web_running = True

    # sys.exit() sesuai untuk aplikasi desktop, tetapi tidak diperlukan
    # untuk menghentikan loop aplikasi yang berjalan di browser.
    def stop_web_game():
        app._web_running = False

    app.quit = stop_web_game

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


asyncio.run(main())
