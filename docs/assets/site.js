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

  document.documentElement.classList.add('js');
  activeNav();
  reveal();
  copyCommands();
})();
