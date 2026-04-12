export function render(html) {
  const app = document.querySelector('#app');
  if (!app) {
    console.error('No #app found');
    return;
  }

  app.innerHTML = html;
}

export function html(strings, ...values) {
  return strings.reduce((accumulator, stringPart, index) => {
    return accumulator + stringPart + (values[index] || '');
  }, '');
}
