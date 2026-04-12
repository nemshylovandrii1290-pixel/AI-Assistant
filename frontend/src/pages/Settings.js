import { html } from '@/shared/lib/dom';
import { MainLayout } from '@/shared/layouts/MainLayout';
import '@/styles/pages/settings.scss';

export function Settings() {
  return MainLayout(html`
    <div class="settings">
      <h2>Settings</h2>
      <p>Тут будуть налаштування.</p>
    </div>
  `);
}
