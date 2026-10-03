/**
 * main.js
 * Lógica do formulário de contato + interações gerais do portfolio.
 * A URL do API Gateway será preenchida após o deploy do backend.
 */

// URL do API Gateway HTTP API (us-east-2)
const API_URL = 'https://n17vr7t1jj.execute-api.us-east-2.amazonaws.com/contact';

// ==========================================
// FORMULÁRIO DE CONTATO
// ==========================================

const form = document.getElementById('contact-form');
const submitBtn = document.getElementById('submit-btn');
const formStatus = document.getElementById('form-status');

/**
 * Valida um campo individualmente.
 * Retorna true se válido, false caso contrário.
 */
function validateField(field) {
  const errorEl = document.getElementById(`${field.id}-error`);
  let message = '';

  if (!field.value.trim()) {
    message = 'Este campo é obrigatório.';
  } else if (field.type === 'email') {
    // Validação básica de formato de e-mail
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(field.value.trim())) {
      message = 'Informe um e-mail válido.';
    }
  } else if (field.id === 'name' && field.value.trim().length < 2) {
    message = 'O nome deve ter pelo menos 2 caracteres.';
  } else if (field.id === 'message' && field.value.trim().length < 10) {
    message = 'A mensagem deve ter pelo menos 10 caracteres.';
  }

  if (message) {
    field.classList.add('invalid');
    if (errorEl) errorEl.textContent = message;
    return false;
  }

  field.classList.remove('invalid');
  if (errorEl) errorEl.textContent = '';
  return true;
}

/**
 * Valida todos os campos do formulário.
 * Retorna true se todos forem válidos.
 */
function validateForm() {
  const name = document.getElementById('name');
  const email = document.getElementById('email');
  const message = document.getElementById('message');

  const nameValid = validateField(name);
  const emailValid = validateField(email);
  const messageValid = validateField(message);

  return nameValid && emailValid && messageValid;
}

/**
 * Exibe o status do formulário (sucesso ou erro).
 */
function showStatus(type, message) {
  formStatus.textContent = message;
  formStatus.className = `form-status ${type}`;
  // Scroll suave até o status
  formStatus.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Limpa o status do formulário.
 */
function clearStatus() {
  formStatus.textContent = '';
  formStatus.className = 'form-status';
}

/**
 * Sanitiza uma string removendo caracteres potencialmente perigosos.
 * O backend também valida — esta é uma camada adicional no cliente.
 */
function sanitize(str) {
  return str.trim().slice(0, 2000);
}

// Validação em tempo real ao sair do campo
['name', 'email', 'message'].forEach((id) => {
  const field = document.getElementById(id);
  if (field) {
    field.addEventListener('blur', () => validateField(field));
    field.addEventListener('input', () => {
      if (field.classList.contains('invalid')) {
        validateField(field);
      }
    });
  }
});

// Submit do formulário
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearStatus();

    if (!validateForm()) return;

    // Verificação de segurança: não enviar se a URL ainda não foi configurada
    if (API_URL === 'SUBSTITUIR_PELA_URL_DO_API_GATEWAY') {
      showStatus('error', 'Formulário ainda não configurado. Tente novamente em breve.');
      return;
    }

    const name = sanitize(document.getElementById('name').value);
    const email = sanitize(document.getElementById('email').value);
    const message = sanitize(document.getElementById('message').value);

    // Estado de carregamento
    submitBtn.disabled = true;
    submitBtn.textContent = 'Enviando...';

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, message }),
      });

      if (response.ok) {
        showStatus('success', '✓ Mensagem enviada com sucesso! Responderei em breve.');
        form.reset();
        // Limpar classes de validação
        ['name', 'email', 'message'].forEach((id) => {
          document.getElementById(id)?.classList.remove('invalid');
        });
      } else {
        // Tentar ler mensagem de erro do backend
        let errorMsg = 'Erro ao enviar. Tente novamente.';
        try {
          const data = await response.json();
          if (data.message) errorMsg = data.message;
        } catch (_) {
          // Ignorar erro de parse
        }
        showStatus('error', errorMsg);
      }
    } catch (err) {
      // Erro de rede
      showStatus('error', 'Falha na conexão. Verifique sua internet e tente novamente.');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Enviar mensagem';
    }
  });
}

// ==========================================
// NAVEGAÇÃO ATIVA
// ==========================================

/**
 * Destaca o link de navegação da seção visível no momento.
 */
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a');

function updateActiveNav() {
  let current = '';
  sections.forEach((section) => {
    const sectionTop = section.offsetTop - 100;
    if (window.scrollY >= sectionTop) {
      current = section.getAttribute('id');
    }
  });

  navLinks.forEach((link) => {
    link.style.color = '';
    if (link.getAttribute('href') === `#${current}`) {
      link.style.color = 'var(--color-text)';
    }
  });
}

window.addEventListener('scroll', updateActiveNav, { passive: true });
updateActiveNav();
