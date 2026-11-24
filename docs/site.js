
const menu=document.querySelector('.menu');
const nav=document.querySelector('nav');
function closeMenu(){nav.classList.remove('open');menu.setAttribute('aria-expanded','false');}
menu.addEventListener('click',()=>menu.setAttribute('aria-expanded',String(nav.classList.toggle('open'))));
nav.addEventListener('click',event=>{if(event.target.closest('a'))closeMenu();});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&nav.classList.contains('open')){closeMenu();menu.focus();}});
document.querySelectorAll('[data-service]').forEach(link=>link.addEventListener('click',()=>{document.querySelector('#service').value=link.dataset.service;}));
const inquiry = document.querySelector('#inquiry');
const requestedService = new URLSearchParams(location.search).get('service');
const serviceSelect = document.querySelector('#service');
if (serviceSelect && Array.from(serviceSelect.options).some(option => option.value === requestedService)) {
 serviceSelect.value = requestedService;
}
inquiry?.addEventListener('submit', async event => {
 event.preventDefault();
 const status = inquiry.querySelector('.status');
 const submit = inquiry.querySelector('button[type="submit"]');
 if (submit.disabled || !inquiry.reportValidity()) return;
 submit.disabled = true;
 inquiry.setAttribute('aria-busy', 'true');
 status.textContent = '상담을 접수하는 중입니다.';
 try {
  const response = await fetch(inquiry.action, {
   method: 'POST',
   headers: {'Content-Type': 'application/json'},
   body: JSON.stringify(Object.fromEntries(new FormData(inquiry)))
  });
  const result = await response.json();
  if (!response.ok || result.received !== true) throw new Error('Submission failed');
  inquiry.reset();
  status.textContent = '상담 신청이 접수되었습니다.';
 } catch {
  status.textContent = '접수를 확인하지 못했습니다. 다시 시도하거나 010-9009-6837로 문의해 주세요.';
 } finally {
  inquiry.removeAttribute('aria-busy');
  submit.disabled = false;
 }
});
if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
 const observer = new IntersectionObserver(entries => {
  for (const entry of entries) {
   if (!entry.isIntersecting) continue;
   entry.target.classList.add('in');
   observer.unobserve(entry.target);
  }
 }, {threshold: 0.12});
 document.querySelectorAll('main section:not(.hero) .wrap').forEach(section => {
  section.classList.add('reveal');
  observer.observe(section);
 });
}
