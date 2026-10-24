import sys,asyncio
from playwright.sync_api import sync_playwright
urls=sys.argv[1:]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    for u in urls:
        pg=b.new_page(viewport=dict(width=1400,height=1000))
        try:
            pg.goto(u,wait_until="networkidle",timeout=45000)
        except Exception as e: print("ERR goto",u,e)
        pg.wait_for_timeout(2500)
        t=pg.inner_text("body")
        name=u.split("//")[1].replace("/","_").strip("_")
        open(f"raw/{name}.txt","w").write(t)
        print(u,len(t))
    b.close()
