from playwright.sync_api import sync_playwright
import re
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_page(viewport=dict(width=1400,height=1000))
    pg.goto("https://buttondown.com/pricing",wait_until="domcontentloaded");pg.wait_for_timeout(3000)
    for v in (1,2,10,20,30,34,35,36,56,57):
        pg.evaluate("""(i)=>{const e=document.querySelector('input[type=range]');const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;s.call(e,i);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}""",v)
        pg.wait_for_timeout(500)
        t=re.sub(r"\s+"," ",pg.inner_text("body"))
        a=t.find("If you have");a=a if a>=0 else t.find("subscribers")
        i=t.find("Buttondown will cost you")
        print(v,t[max(0,i-200):i+90])
    b.close()
