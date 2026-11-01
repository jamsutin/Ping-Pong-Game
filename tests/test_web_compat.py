"""Regression test statis: kode game tidak boleh bergantung pada hal yang
tidak ada di runtime WebAssembly Pygbag.

Bug nyata yang pernah lolos meski GitHub Actions "success":
  * `import wave` tanpa try/except -> ModuleNotFoundError saat import di browser
  * `pygame.event.init()` -> AttributeError (tidak ada di pygame-ce)
  * `pygame.SCALED` di browser -> "pygame.error: failed to create renderer"
"""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = ["main.py", "ping_pong_cinematic.py"]

# Modul stdlib yang tidak tersedia / tidak dapat diandalkan di CPython WASM Pygbag.
NOT_IN_WASM = {"wave", "audioop", "tkinter", "multiprocessing", "sqlite3", "ssl", "curses"}


def _tree(name):
    return ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)


def _toplevel_unguarded_imports(tree):
    """Import di level modul yang TIDAK dibungkus try/except."""
    found = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            found += [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append(node.module.split(".")[0])
    return found


def test_no_unguarded_wasm_incompatible_imports():
    for name in FILES:
        bad = sorted(set(_toplevel_unguarded_imports(_tree(name))) & NOT_IN_WASM)
        assert not bad, f"{name}: import level-modul tak tersedia di browser (bungkus try/except): {bad}"


def test_no_pygame_event_init():
    for name in FILES:
        src = (ROOT / name).read_text(encoding="utf-8")
        assert "pygame.event.init" not in src, f"{name}: pygame.event.init() tidak ada di pygame-ce"


def test_scaled_flag_is_disabled_in_web_mode():
    src = (ROOT / "ping_pong_cinematic.py").read_text(encoding="utf-8")
    scaled_line = [i for i, l in enumerate(src.splitlines()) if '"SCALED"' in l]
    assert scaled_line, "pemakaian SCALED tidak ditemukan"
    window = "\n".join(src.splitlines()[max(0, scaled_line[0] - 6): scaled_line[0] + 1])
    assert "WEB_MODE" in window, "SCALED harus dilewati saat WEB_MODE (browser)"


def test_main_emits_boot_checkpoints():
    src = (ROOT / "main.py").read_text(encoding="utf-8")
    for cp in ["main.py imported", "pygame imported", "Game module imported",
               "Pygame display initialized", "Fonts initialized", "Game object created",
               "First frame drawn", "Game loop running"]:
        assert cp in src, f"checkpoint '[BOOT] {cp}' hilang dari main.py"


if __name__ == "__main__":
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        fn()
        print("OK", fn.__name__)
