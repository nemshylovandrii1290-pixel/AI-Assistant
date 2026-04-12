import { render } from '@/shared/lib/dom';

const routes = {};

export function registerRoute(path, component) {
  routes[path] = component;
}

export function navigate(path) {
  window.history.pushState({}, '', path);
  renderRoute(path);
}

export function initRouter() {
  window.addEventListener('popstate', () => {
    renderRoute(window.location.pathname);
  });
}

export function refreshRoute() {
  renderRoute(window.location.pathname);
}

function renderRoute(path) {
  const component = routes[path] ?? routes['/'];
  if (!component) return;

  render(component());
}
