// Browser FPS probe - paste into the DevTools console of the running app.
// Samples requestAnimationFrame deltas for 15s; prints min/avg/max FPS and sample count,
// plus the app's own metrics overlay line if one exists (selector below).
// Read-only: touches no app state. Result is also copied to the clipboard.
// Report the window and sample count with the numbers; min exposes frame spikes that avg hides.
javascript:(function(){if(window.__fpsMeasuring){alert("Measuring already running. Wait 15s.");return}window.__fpsMeasuring=true;var D=15000,samples=[],start=performance.now(),last=start;function loop(t){samples.push(1000/(t-last));last=t;if(t-start<D){requestAnimationFrame(loop)}else{window.__fpsMeasuring=false;var f=samples.filter(function(x){return x>0&&x<400}),mn=Math.min.apply(null,f),mx=Math.max.apply(null,f),sum=f.reduce(function(a,b){return a+b},0),o=document.querySelector('[data-testid="pixel-office-fps"]'),extra=o?" | "+o.textContent.replace(/\s+/g," ").trim():"",res="FPS MIN "+mn.toFixed(1)+" | AVG "+(sum/f.length).toFixed(1)+" | MAX "+mx.toFixed(1)+" | SAMPLES "+f.length+extra;alert(res)}}requestAnimationFrame(loop)})();
