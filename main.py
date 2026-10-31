"""Entrypoint browser untuk Pygbag.

Versi desktop tetap dijalankan melalui:
    python ping_pong_cinematic.py

Pygbag membutuhkan main.py dan event loop asynchronous. Kode permainan
tetap menggunakan kelas Game yang sama dari ping_pong_cinematic.py.
"""
import asyncio

import pygame

import ping_pong_cinematic as game


async def main():
    pygame.mixer.pre_init(game.SAMPLE_RATE, -16, 1, 512)
    pygame.init()

    app = game.Game()

    while True:
        app.handle_events()
        app.update()
        app.draw()
        pygame.display.flip()
        app.clock.tick(game.FPS)

        # Wajib: beri kesempatan browser memproses input dan menggambar frame.
        await asyncio.sleep(0)


asyncio.run(main())
