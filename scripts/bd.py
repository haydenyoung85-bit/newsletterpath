from playwright.sync_api import sync_playwright
import re
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_page(viewport=dict(width=1400,height=1000))
    pg.goto("https://buttondown.com/pricing",wait_until="domcontentloaded");pg.wait_for_timeout(3000)
    prev=None
    for v in range(0,101):
        pg.evaluate("""(i)=>{const e=document.querySelector('input[type=range]');const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;s.call(e,i);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}""",v)
        pg.wait_for_timeout(200)
        t=pg.inner_text("body")
        a=t.find("Buttondown will cost you:");z=t.find("That price includes")
        s=re.sub(r"\s+"," ",t[a:z])
        if s!=prev: print(v,s[:200]);prev=s;pg.screenshot(path=f"raw/bd_{v}.png",clip=dict(x=300,y=150,width=800,height=400))
    b.close()
