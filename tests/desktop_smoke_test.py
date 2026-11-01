"""Smoke test versi desktop tanpa jendela/audio nyata (driver SDL dummy).

Membuktikan perubahan untuk browser tidak merusak `python ping_pong_cinematic.py`:
modul bisa di-import, Game() dibuat dengan audio sintetis aktif, dan beberapa
frame update+draw berjalan tanpa exception.
"""
import os
import sys
import pathlib

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402
import ping_pong_cinematic as game  # noqa: E402


def test_desktop_game_runs_frames():
    assert not getattr(game, "WEB_MODE", False), "desktop tidak boleh dalam WEB_MODE"
    assert game.wave is not None, "modul wave harus tersedia di desktop (audio sintetis)"
    pygame.init()
    app = game.Game()
    assert app.screen.get_size() == (game.SCREEN_W, game.SCREEN_H)
    for _ in range(120):
        app.update()
        app.draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    test_desktop_game_runs_frames()
    print("OK desktop_smoke")
