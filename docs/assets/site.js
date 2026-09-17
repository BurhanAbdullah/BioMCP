(() => {
  const reveal = () => {
    const items = document.querySelectorAll('.reveal');
    if (!items.length || !('IntersectionObserver' in window)) {
      items.forEach(item => item.classList.add('is-visible'));
      return;
    }
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    items.forEach(item => observer.observe(item));
  };

  const copyCommands = () => {
    document.querySelectorAll('[data-copy]').forEach(button => {
      button.addEventListener('click', async () => {
        const target = document.querySelector(button.dataset.copy);
        if (!target) return;
        const text = target.innerText.trim();
        try {
          await navigator.clipboard.writeText(text);
          const original = button.textContent;
          button.textContent = 'Copied';
          setTimeout(() => { button.textContent = original; }, 1200);
        } catch (_) {
          button.textContent = 'Select to copy';
          setTimeout(() => { button.textContent = 'Copy'; }, 1200);
        }
      });
    });
  };

  const activeNav = () => {
    const page = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.navlinks a[href]').forEach(link => {
      const href = link.getAttribute('href');
      if (href && !href.startsWith('http') && href.split('#')[0] === page) {
        link.setAttribute('aria-current', 'page');
      }
    });
  };

  const mobileNav = () => {
    const nav = document.querySelector('.nav');
    const links = document.querySelector('.navlinks');
    if (!nav || !links || nav.querySelector('.nav-toggle')) return;

    const style = document.createElement('style');
    style.textContent = `
      .nav-toggle{display:none;min-height:38px;padding:0 13px;border:1px solid #d8cdd0;border-radius:6px;background:#fff;color:#7f1325;font:700 13px Inter,ui-sans-serif,system-ui,sans-serif;cursor:pointer}
      @media(max-width:900px){
        .nav{position:relative;align-items:center}
        .nav-toggle{display:inline-flex;align-items:center;justify-content:center}
        .navlinks{display:none;position:absolute;left:18px;right:18px;top:calc(100% + 1px);padding:10px;background:#fff;border:1px solid #ded9da;border-top:0;box-shadow:0 14px 28px rgba(52,24,29,.10);z-index:30}
        .navlinks.is-open{display:flex;flex-direction:column;align-items:stretch}
        .navlinks a{width:100%;padding:10px 12px}
        .nav-github{display:block!important}
      }
    `;
    document.head.appendChild(style);

    const toggle = document.createElement('button');
    toggle.className = 'nav-toggle';
    toggle.type = 'button';
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-controls', 'site-navlinks');
    toggle.textContent = 'Menu';
    links.id = 'site-navlinks';
    nav.appendChild(toggle);

    const close = () => {
      links.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = 'Menu';
    };

    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.textContent = open ? 'Close' : 'Menu';
    });

    links.querySelectorAll('a').forEach(link => link.addEventListener('click', close));
    window.addEventListener('resize', () => {
      if (window.innerWidth > 900) close();
    });
  };

  const filters = () => {
    document.querySelectorAll('[data-filter-target]').forEach(input => {
      const target = document.querySelector(input.dataset.filterTarget);
      if (!target) return;
      const items = Array.from(target.querySelectorAll('[data-filter-item]'));
      const empty = document.createElement('p');
      empty.className = 'filter-empty';
      empty.textContent = 'No matching results. Try a broader search.';
      empty.hidden = true;
      target.parentNode.insertBefore(empty, target.nextSibling);

      input.addEventListener('input', () => {
        const query = input.value.trim().toLowerCase();
        let visible = 0;
        items.forEach(item => {
          const match = query === '' || item.textContent.toLowerCase().includes(query);
          item.hidden = !match;
          if (match) visible += 1;
        });
        empty.hidden = visible !== 0;
      });
    });
  };

  document.documentElement.classList.add('js');
  activeNav();
  mobileNav();
  reveal();
  copyCommands();
  filters();
})();
