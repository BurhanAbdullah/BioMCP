(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  const reveal = () => {
    const items = $$('.reveal');
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

  const activeNav = () => {
    const page = location.pathname.split('/').pop() || 'index.html';
    $$('.navlinks a[href]').forEach(link => {
      const href = link.getAttribute('href');
      if (href && !href.startsWith('http') && href.split('#')[0] === page) link.setAttribute('aria-current', 'page');
    });
  };

  const mobileNav = () => {
    const nav = $('.nav');
    const links = $('.navlinks');
    if (!nav || !links || $('.nav-toggle', nav)) return;
    const toggle = document.createElement('button');
    toggle.className = 'nav-toggle';
    toggle.type = 'button';
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-controls', 'site-navlinks');
    toggle.textContent = 'Menu';
    links.id = 'site-navlinks';
    nav.appendChild(toggle);
    const close = () => { links.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); toggle.textContent = 'Menu'; };
    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.textContent = open ? 'Close' : 'Menu';
    });
    $$('a', links).forEach(link => link.addEventListener('click', close));
    window.addEventListener('resize', () => { if (window.innerWidth > 900) close(); });
  };

  const copyButtons = () => {
    $$('[data-copy]').forEach(button => button.addEventListener('click', async () => {
      const target = $(button.dataset.copy);
      if (!target) return;
      const text = target.dataset.copyText || $$('.command', target).map(node => node.textContent.trim()).filter(Boolean).join('\n') || target.textContent.trim();
      if (!text) return;
      const original = button.textContent;
      try {
        await navigator.clipboard.writeText(text);
        button.textContent = 'Copied';
      } catch (_) {
        button.textContent = 'Select to copy';
      }
      setTimeout(() => { button.textContent = original; }, 1200);
    }));
  };

  const registryData = async () => {
    const response = await fetch('assets/registry.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`Registry request failed: ${response.status}`);
    const data = await response.json();
    return Array.isArray(data.servers) ? data.servers : [];
  };

  const renderServerCards = (servers, grid, empty, input) => {
    const query = input ? input.value.trim().toLowerCase() : '';
    const matches = servers.filter(server => JSON.stringify(server).toLowerCase().includes(query));
    grid.innerHTML = '';
    matches.forEach(server => {
      const article = document.createElement('article');
      article.className = 'card server-card reveal is-visible';
      const state = server.status === 'validated' ? 'validated' : server.status === 'experimental' ? 'experimental' : '';
      const status = server.status ? server.status.charAt(0).toUpperCase() + server.status.slice(1) : 'Unspecified';
      const scope = server.installable ? 'Installable' : server.external ? 'External' : 'Not installable';
      const tools = Array.isArray(server.tools) && server.tools.length ? server.tools.join(', ') : 'No tools listed';
      article.innerHTML = '<span class="badge server-status"></span><h3></h3><p class="registry-description"></p><p class="registry-command-line"><span class="code-inline registry-command"></span></p><p class="kicker registry-tools"></p>';
      $('.server-status', article).className = `badge server-status ${state}`;
      $('.server-status', article).textContent = `${status} / ${scope}`;
      $('h3', article).textContent = server.display_name || server.name;
      $('.registry-description', article).textContent = server.description || 'No description is currently provided.';
      $('.registry-command', article).textContent = server.command || 'No command listed';
      $('.registry-tools', article).textContent = `Tools: ${tools}`;
      grid.appendChild(article);
    });
    if (empty) empty.hidden = matches.length !== 0;
  };

  const registry = async () => {
    const grid = $('#server-grid');
    if (!grid) return;
    const input = $('[data-registry-filter]');
    const empty = $('[data-registry-empty]');
    try {
      const servers = await registryData();
      const render = () => renderServerCards(servers, grid, empty, input);
      if (input) input.addEventListener('input', render);
      render();
      const total = $('#registry-total');
      const validated = $('#registry-validated');
      const experimental = $('#registry-experimental');
      if (total) total.textContent = servers.length;
      if (validated) validated.textContent = servers.filter(s => s.status === 'validated').length;
      if (experimental) experimental.textContent = servers.filter(s => s.status === 'experimental').length;
    } catch (_) {
      grid.innerHTML = '<p class="kicker">The registry could not be loaded. The repository registry remains the authoritative source.</p>';
      if (empty) empty.hidden = true;
    }
  };

  const homeRegistry = async () => {
    const grid = $('#home-server-grid');
    if (!grid) return;
    try {
      const servers = await registryData();
      const active = servers.filter(server => server.status === 'validated' || server.status === 'experimental').slice(0, 4);
      grid.innerHTML = '';
      active.forEach(server => {
        const article = document.createElement('article');
        article.className = 'card server-card reveal is-visible';
        const state = server.status === 'validated' ? 'validated' : 'experimental';
        article.innerHTML = '<span class="badge server-status"></span><h3></h3><p></p><a class="text-link" href="servers.html">View registry details</a>';
        $('.server-status', article).className = `badge server-status ${state}`;
        $('.server-status', article).textContent = `${server.status.charAt(0).toUpperCase() + server.status.slice(1)} / ${server.installable ? 'Installable' : 'External'}`;
        $('h3', article).textContent = server.display_name || server.name;
        $('p', article).textContent = server.description || 'No description is currently provided.';
        grid.appendChild(article);
      });
    } catch (_) {
      grid.innerHTML = '<p class="kicker">The current server registry is available on the Servers page.</p>';
    }
  };

  const installBuilder = async () => {
    const root = $('#install-builder');
    if (!root) return;
    try {
      const servers = (await registryData()).filter(s => s.installable);
      const serverBox = $('[data-install-servers]', root);
      const client = $('[data-install-client]', root);
      const output = $('#install-preview');
      const render = () => {
        const selected = $$('input:checked', serverBox).map(input => input.value);
        const clientName = client.value;
        const command = `biomcp install --servers ${selected.join(',') || 'none'} --clients ${clientName}`;
        output.textContent = command;
        output.dataset.copyText = command;
      };
      serverBox.innerHTML = '';
      servers.forEach((server, index) => {
        const label = document.createElement('label');
        label.className = 'choice';
        label.innerHTML = `<input type="checkbox" value="${server.name}" ${index === 0 ? 'checked' : ''}><span><strong></strong><small></small></span>`;
        $('strong', label).textContent = server.display_name || server.name;
        $('small', label).textContent = server.description || '';
        serverBox.appendChild(label);
      });
      serverBox.addEventListener('change', render);
      client.addEventListener('change', render);
      render();
    } catch (_) {
      const output = $('#install-preview');
      if (output) output.textContent = 'Registry unavailable. Use biomcp list to inspect available servers.';
    }
  };

  const clientBuilder = () => {
    const root = $('#client-builder');
    if (!root) return;
    const client = $('[data-client-choice]', root);
    const server = $('[data-client-server]', root);
    const output = $('#client-preview');
    const render = () => {
      const command = server.value || 'biomcp-bioimage';
      if (client.value === 'codex') {
        output.textContent = `[mcp_servers.${command.replace(/[^a-z0-9_]/gi, '_')}]\ncommand = "${command}"`;
      } else {
        output.textContent = JSON.stringify({ mcpServers: { biomcp: { command, args: [] } } }, null, 2);
      }
      output.dataset.copyText = output.textContent;
    };
    client.addEventListener('change', render);
    server.addEventListener('change', render);
    render();
  };

  const examples = () => {
    const tabs = $$('[data-example-tab]');
    if (!tabs.length) return;
    const panels = $$('[data-example-panel]');
    const activate = name => {
      tabs.forEach(tab => { const active = tab.dataset.exampleTab === name; tab.classList.toggle('is-active', active); tab.setAttribute('aria-selected', String(active)); });
      panels.forEach(panel => { panel.hidden = panel.dataset.examplePanel !== name; });
    };
    tabs.forEach(tab => tab.addEventListener('click', () => activate(tab.dataset.exampleTab)));
    activate(tabs[0].dataset.exampleTab);
  };

  const checklist = () => {
    const root = $('#contributor-checklist');
    if (!root) return;
    const checks = $$('input[type="checkbox"]', root);
    const count = $('#checklist-count');
    const update = () => { const done = checks.filter(input => input.checked).length; if (count) count.textContent = `${done} of ${checks.length} complete`; };
    checks.forEach(input => input.addEventListener('change', update));
    update();
  };

  document.documentElement.classList.add('js');
  activeNav();
  mobileNav();
  copyButtons();
  registry();
  homeRegistry();
  installBuilder();
  clientBuilder();
  examples();
  checklist();
  reveal();
})();
