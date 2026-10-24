from playwright.sync_api import sync_playwright
import re
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_page(viewport=dict(width=1400,height=1000))
    pg.goto("https://www.mailerlite.com/pricing",wait_until="domcontentloaded");pg.wait_for_timeout(3000)
    try: pg.click("text=Reject all",timeout=3000)
    except: pass
    for mode in ["Billed monthly","Billed yearly"]:
        try: pg.click(f"text={mode}",timeout=3000)
        except Exception as e: print("noclick",mode)
        for n in ["1000","5000"]:
            pg.fill("#subscriber-count",n);pg.keyboard.press("Enter");pg.wait_for_timeout(1500)
            t=pg.inner_text("body")
            i=t.find("Comfort $")
            print(mode,n,"|",t[i:i+120].replace("\n"," "))
            j=t.find("Go unlimited");print(t[j:j+420].replace("\n"," | "))
    b.close()
