from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_page(viewport=dict(width=1400,height=1000))
    pg.goto("https://ghost.org/pricing/",wait_until="domcontentloaded");pg.wait_for_timeout(3000)
    for mode in ["Monthly billing","Yearly billing"]:
        pg.click(f"text={mode}");pg.wait_for_timeout(500)
        for i in range(0,10):
            pg.evaluate("""(i)=>{const e=document.getElementById('members');const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;s.call(e,i);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}""",i)
            pg.wait_for_timeout(500)
            t=pg.inner_text("body")
            a=t.find("Based on an audience");z=t.find("Feature comparison")
            print(mode,i,t[a:z].replace("\n"," ").replace("\t"," ")[:420])
    b.close()
