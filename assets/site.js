/* Encontrarás Tudo — comportamento compartilhado */
(function(){
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(!reduce){ document.documentElement.classList.add('js'); }

  // Nav: transparente/escuro -> sólido ao rolar
  var nav = document.getElementById('nav');
  var hero = document.querySelector('.hero, .page-hero');
  if(nav){
    var onScroll = function(){
      var th = hero ? hero.offsetHeight - 72 : 40;
      if(window.scrollY > th){ nav.classList.add('scrolled'); } else { nav.classList.remove('scrolled'); }
    };
    window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
  }

  // Menu mobile
  var tog = document.getElementById('menuToggle'), menu = document.getElementById('menu');
  if(tog && menu){
    tog.addEventListener('click', function(){
      var open = menu.classList.toggle('open');
      tog.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    menu.querySelectorAll('a').forEach(function(a){
      a.addEventListener('click', function(){ menu.classList.remove('open'); tog.setAttribute('aria-expanded','false'); });
    });
  }

  // Reveal on scroll
  if(!reduce && 'IntersectionObserver' in window){
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
    }, {threshold:.12, rootMargin:'0px 0px -8% 0px'});
    document.querySelectorAll('.reveal').forEach(function(el){ io.observe(el); });
  }

  function okEmail(e){ return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e); }

  /* Config injetada pelo gerador (window.ET_CFG vem do config.json) */
  var CFG = window.ET_CFG || {};
  var LISTMONK_URL = CFG.listmonk || "https://lista.encontrarastudo.com.br";
  var LISTA_UUID = CFG.listUuid || "";
  function subscribe(email, nome){
    if(LISTA_UUID && LISTA_UUID.indexOf('__')===-1){
      try{ fetch(LISTMONK_URL+'/api/public/subscription', {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({email:email, name:nome||'', list_uuids:[LISTA_UUID]})}); }catch(e){}
    }
  }

  // Newsletter (inline)
  var nlForm = document.getElementById('nlForm');
  if(nlForm){
    var nlDone = document.getElementById('nlDone'), nlEmail = document.getElementById('nlEmail'),
        nlNome = document.getElementById('nlNome');
    nlForm.addEventListener('submit', function(ev){
      ev.preventDefault();
      if(!okEmail(nlEmail.value.trim())){ nlEmail.focus(); nlEmail.style.borderColor='#9a2520'; return; }
      subscribe(nlEmail.value.trim(), nlNome ? nlNome.value : '');
      nlForm.style.display='none'; if(nlDone) nlDone.classList.add('show');
    });
  }

  // Landing da isca (guia)
  var form = document.getElementById('form');
  if(form){
    var card = document.getElementById('card'), done = document.getElementById('done'),
        errEl = document.getElementById('err'), emailEl = document.getElementById('email');
    form.addEventListener('submit', function(ev){
      ev.preventDefault(); if(errEl) errEl.textContent='';
      var email = emailEl.value.trim(), nome = (document.getElementById('nome')||{}).value || '';
      if(!okEmail(email)){ if(errEl) errEl.textContent='Digite um e-mail válido para receber o guia.'; emailEl.focus(); return; }
      subscribe(email, nome);
      if(card) card.classList.add('success'); if(done) done.classList.add('show');
      if(card) card.scrollIntoView({behavior:'smooth', block:'center'});
    });
  }

  // Contato (mensagem — mostra confirmação)
  var ctForm = document.getElementById('ctForm');
  if(ctForm){
    var ctDone = document.getElementById('ctDone');
    ctForm.addEventListener('submit', function(ev){
      ev.preventDefault();
      ctForm.style.display='none'; if(ctDone) ctDone.classList.add('show');
    });
  }
})();
