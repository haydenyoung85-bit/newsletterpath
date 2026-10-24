import sys
from playwright.sync_api import sync_playwright
u=sys.argv[1]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_page(viewport=dict(width=1400,height=1000))
    try: pg.goto(u,wait_until="domcontentloaded",timeout=45000)
    except Exception as e: print("ERR",e)
    pg.wait_for_timeout(4000)
    print(pg.evaluate("""()=>[...document.querySelectorAll('input,[role=slider]')].map(e=>({t:e.tagName,type:e.type,min:e.min,max:e.max,step:e.step,val:e.value,id:e.id,name:e.name,cls:(e.className||'').toString().slice(0,60),aria:e.getAttribute('aria-valuenow')+'/'+e.getAttribute('aria-valuemax')}))"""))
    b.close()
