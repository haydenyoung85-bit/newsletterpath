(function(){var f=document.getElementById("nl");if(!f||!window.fetch)return;var m=document.getElementById("nlmsg");
f.addEventListener("submit",function(e){e.preventDefault();var b=f.querySelector("button");b.disabled=true;m.textContent="Sending…";
fetch(f.action,{method:"POST",body:new FormData(f),headers:{Accept:"application/json"}}).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(j){
if(j&&j.redirect_url&&/confirm/i.test(j.redirect_url)){m.textContent="Almost done: check your inbox to confirm."}else{m.textContent="Thanks! Check your inbox to confirm."}f.reset();b.disabled=false}).catch(function(){m.textContent="Could not subscribe here. Try again later.";b.disabled=false})})})();
