/* ENERGY V23 - robust Plotly double-click reset bridge.
   Uses Dash's supported clientside set_props API to update a dcc.Store.
   This avoids relying on a synthetic click on a hidden React button.
*/
(function () {
  function bind(graph) {
    if (!graph || graph.__energyV23Bound) return;
    graph.__energyV23Bound = true;
    graph.on('plotly_doubleclick', function () {
      try {
        if (window.dash_clientside && typeof window.dash_clientside.set_props === 'function') {
          window.dash_clientside.set_props('graph-reset-signal', {data: Date.now()});
        }
      } catch (e) {
        console.warn('ENERGY V23 reset bridge:', e);
      }
    });
  }
  function scan() { document.querySelectorAll('.js-plotly-plot').forEach(bind); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scan); else scan();
  new MutationObserver(scan).observe(document.body, {childList:true, subtree:true});
  setTimeout(scan,250); setTimeout(scan,1000); setTimeout(scan,2500);
})();
