"""HTTP and responsive browser smoke tests for N.I. SINOTTICA.
Runs on GitHub Actions, screenshots retained as workflow artifacts.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess
import time
import urllib.request

root=Path(__file__).resolve().parents[1]
server=subprocess.Popen(["python","-m","http.server","8765","--bind","127.0.0.1"],cwd=root,
                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(30):
        try:
            urllib.request.urlopen("http://127.0.0.1:8765/sinottica.html",timeout=1)
            break
        except Exception:time.sleep(.2)
    else:raise RuntimeError("HTTP server failed")
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        for name,w,h in [("mobile",390,844),("desktop",1440,900)]:
            page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.goto("http://127.0.0.1:8765/sinottica.html",wait_until="domcontentloaded")
            page.wait_for_timeout(3500)
            assert page.locator("#map").count()==1
            assert page.locator("#fronts").is_disabled()
            assert page.locator("#status").inner_text()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth+2"),"horizontal overflow"
            assert not errors,errors
            Path("screenshots").mkdir(exist_ok=True)
            page.screenshot(path=f"screenshots/sinottica-{name}.png",full_page=True)
            page.close()
        browser.close()
finally:
    server.terminate()
