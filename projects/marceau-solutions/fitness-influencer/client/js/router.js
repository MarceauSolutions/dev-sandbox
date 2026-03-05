/* ============================================================
   Hash-based SPA Router — Client Portal
   ============================================================ */

const Router = {
  routes: {},
  currentPage: null,
  currentHash: '',
  container: null,

  init(containerId) {
    this.container = document.getElementById(containerId);
    window.addEventListener('hashchange', () => this.navigate());
    this.navigate();
  },

  register(hash, page) {
    this.routes[hash] = page;
  },

  navigate() {
    const raw = location.hash.slice(1) || '';
    // Strip query params for route matching
    const hash = raw.split('?')[0];

    if (hash === this.currentHash && this.currentPage) return;

    const page = this.routes[hash];
    if (!page) {
      location.hash = '';
      return;
    }

    // Cleanup previous page
    if (this.currentPage && this.currentPage.destroy) {
      this.currentPage.destroy();
    }

    this.currentHash = hash;
    this.currentPage = page;

    // Update sidebar active state
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.page === hash);
    });

    // Update breadcrumb
    const crumb = document.getElementById('breadcrumb-page');
    if (crumb) crumb.textContent = page.title || hash || 'Dashboard';

    // Hide sidebar on mobile after navigation
    if (window.innerWidth <= 768) {
      const sidebar = document.getElementById('sidebar');
      if (sidebar) sidebar.classList.remove('open');
    }

    // Show loading
    this.container.innerHTML = '<div class="loading-overlay"><div class="spinner"></div> Loading...</div>';

    // Init (once) then render
    const doRender = () => {
      try {
        page.render(this.container);
      } catch (err) {
        console.error('Page render error:', err);
        this.container.innerHTML = `<div class="empty-state"><p>Error loading page: ${err.message}</p></div>`;
      }
    };

    if (page.init && !page._initialized) {
      const initWithTimeout = Promise.race([
        Promise.resolve(page.init()),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Page init timeout')), 8000))
      ]);
      initWithTimeout.then(() => {
        page._initialized = true;
        doRender();
      }).catch(err => {
        console.warn('Page init issue:', err.message);
        page._initialized = true;
        doRender();
      });
    } else {
      doRender();
    }
  },

  go(hash) {
    location.hash = hash;
  }
};
