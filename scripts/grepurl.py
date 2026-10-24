import sys,re,requests,html
u,pat=sys.argv[1],sys.argv[2]
r=requests.get(u,headers={"User-Agent":"Mozilla/5.0 (NewsletterPath verifier)"},timeout=30)
t=re.sub(r"<(script|style)[^>]*>.*?</\1>"," ",r.text,flags=re.S);t=html.unescape(re.sub(r"<[^>]+>"," ",t));t=re.sub(r"\s+"," ",t)
print(u,r.status_code,len(t))
for m in list(re.finditer(pat,t,re.I))[:4]:
    print("  ..."+t[max(0,m.start()-150):m.end()+200]+"...")
