import '@/styles/components/header.scss';
import { getBackendStatus } from '@/shared/model/backendStatus';

export function Header() {
  const backend = getBackendStatus();

  return `
    <header class="header">
      <div class="logo">AI Assistant</div>
      <div class="status status--${backend.state}" title="${backend.detail}">${backend.label}</div>
    </header>
  `;
}
