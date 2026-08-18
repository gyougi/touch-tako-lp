// 首屏键盘演示：随机高亮按键并显示对应手指。与 i18n 无关，但依赖当前语言取手指名。
// mockLang 由 build.py 按页面语言注入。
var mockLang=%MOCKLANG%, mockIdx=3; // start on F, matching the static markup
var MOCK_KEYS=[
  {k:'A',fin:{ja:'ひだりの こゆび',    en:'left pinky',   zh:'左手小指'}},
  {k:'S',fin:{ja:'ひだりの くすりゆび', en:'left ring',    zh:'左手无名指'}},
  {k:'D',fin:{ja:'ひだりの なかゆび',  en:'left middle',  zh:'左手中指'}},
  {k:'F',fin:{ja:'ひだりの ひとさし指', en:'left index',   zh:'左手食指'}},
  {k:'G',fin:{ja:'ひだりの ひとさし指', en:'left index',   zh:'左手食指'}},
  {k:'H',fin:{ja:'みぎの ひとさし指',  en:'right index',  zh:'右手食指'}},
  {k:'J',fin:{ja:'みぎの ひとさし指',  en:'right index',  zh:'右手食指'}},
  {k:'K',fin:{ja:'みぎの なかゆび',   en:'right middle', zh:'右手中指'}},
  {k:'L',fin:{ja:'みぎの くすりゆび',  en:'right ring',   zh:'右手无名指'}},
  {k:';',fin:{ja:'みぎの こゆび',     en:'right pinky',  zh:'右手小指'}}
];
function renderMock(){
  var step=MOCK_KEYS[mockIdx];
  var t=document.querySelector('.key-target'); if(!t) return;
  t.textContent=step.k;
  var fin=document.querySelector('.prompt .fin'); if(fin) fin.textContent=step.fin[mockLang]||step.fin.ja;
  document.querySelectorAll('.kbd .key').forEach(function(el,i){ el.classList.toggle('tk', i===mockIdx); });
}
renderMock();   // 初期表示（動きを減らす設定でもここは通す）

(function(){
  // Respect users who prefer reduced motion — leave it on a static "F".
  if(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  function nextKey(){
    var n; do { n=Math.floor(Math.random()*MOCK_KEYS.length); } while(n===mockIdx);
    mockIdx=n;
    renderMock();
    var t=document.querySelector('.key-target');
    if(t&&t.animate) t.animate([{transform:'scale(.8)'},{transform:'scale(1.07)'},{transform:'scale(1)'}],{duration:340,easing:'cubic-bezier(.2,.8,.3,1)'});
    setTimeout(nextKey, 850+Math.random()*750); // varied cadence, like real typing
  }
  setTimeout(nextKey, 1200);
})();
