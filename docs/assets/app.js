(function(){
var $=function(s,r){return(r||document).querySelector(s)},$$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
function money(v){if(v===null||v===undefined||v==="")return"–";v=+v;return"$"+(v%1?v.toFixed(2).replace(/0$/,""):v)}
function fnum(n){return(+n).toLocaleString("en-US")}
var pt=$("#pt");
if(pt){
 var size=$("#size"),sort=$("#sort"),bill=$("#bill"),tb=pt.tBodies[0],note=$("#note"),base=note&&note.textContent;
 var rows=$$("tr",tb);
 function val(r,k){var d=r.dataset;if(k==="name")return d.name.toLowerCase();var b=bill.value;
  if(k==="p1")return +(d[b+"1"]||d.m1);if(k==="p5")return +(d[b+"5"]||d.m5);
  if(k==="free")return d.freeall==="1"?1e9:+d.free;if(k==="fee")return d.fee===""?99:+d.fee}
 function render(){
  var n=+size.value,b=bill.value;
  rows.forEach(function(r){var d=r.dataset;
   $$("td.p",r).forEach(function(c){var k=c.dataset.n;c.textContent=money(d[b+k]||d["m"+k])});
   var ok=d.freeall==="1"||(+d.free>=n&&+d.free>0),e=$("em.ok",r);e.hidden=!ok;r.classList.toggle("hl",ok)});
  var k=sort.value,desc=(k==="free");
  rows.sort(function(a,c){var x=val(a,k),y=val(c,k);return(x<y?-1:x>y?1:0)*(desc?-1:1)||(val(a,"name")<val(c,"name")?-1:1)});
  rows.forEach(function(r){tb.appendChild(r)});
  note.textContent=(n>5000?"Your size is above 5,000, so the 5,000 prices are a floor; check each vendor's slider. ":n<=1000?"":"Between 1,000 and 5,000 prices rise by tier; see the 5,000 column as the upper bound. ")+base;
  $$("#pl li").forEach(function(li){var h=li.dataset.hard,e=$("em",li);
   if(h===""){e.textContent="unknown";e.className=""}
   else if(n>=+h){e.textContent="open";e.className="open"}
   else{e.textContent="needs "+fnum(h);e.className="no"}})};
 [size,sort,bill].forEach(function(e){e.addEventListener("change",render)});
 $$("thead th[data-k]",pt).forEach(function(th){th.addEventListener("click",function(){sort.value=th.dataset.k;render()})});
 render();
}
var at=$("#at");
if(at){var sz=$("#size");sz.addEventListener("change",function(){var n=+sz.value;
 $$("tbody tr",at).forEach(function(r){var h=r.dataset.hard;r.style.opacity=(sz.value&&h!==""&&+h>n)?".4":"1"})})}
var cr=$("#cr");
if(cr&&window.NP){
 var cl=$("#cl"),cn=$("#cn"),cp=$("#cp");
 function calc(){var k=cl.value,rev=Math.max(0,+cn.value)*Math.max(0,+cp.value),out=[];
  NP.platforms.forEach(function(p){if(p.charge_plan===null||p.charge_plan===undefined||p.id==="flodesk")return;
   var plan=p["charge_m"+k];if(plan===undefined||plan===null)plan=p["m"+k];
   var cost=plan+(p.fee_pct||0)/100*rev;out.push({n:p.name+(p.charge_unconfirmed?" *":""),c:cost,plan:plan,fee:(p.fee_pct||0)/100*rev})});
  out.sort(function(a,b){return a.c-b.c});
  cr.innerHTML=out.map(function(o){return"<li><b>"+money(o.c)+"</b> "+o.n+" <span class=sm>(plan "+money(o.plan)+" + fee "+money(o.fee)+")</span></li>"}).join("")}
 [cl,cn,cp].forEach(function(e){e.addEventListener("input",calc)});calc();
}
})();
