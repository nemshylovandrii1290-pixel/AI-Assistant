import { Header } from '@/shared/ui/Header';
import { Sidebar } from '@/shared/ui/Sidebar';
import '@/styles/layout/app.scss';

export function MainLayout(content) {
  return `
    <div class="app">
      ${Header()}

      <div class="body">
        ${Sidebar()}
        <main class="content">
          ${content}
        </main>
      </div>
    </div>
  `;
}
