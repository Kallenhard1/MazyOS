#!/bin/bash
# SessionStart hook — garante o WeasyPrint disponível pra renderizar PDFs
# (propostas, diagnósticos, apresentações) nas sessões do Claude Code na web.
set -euo pipefail

# Só roda no ambiente remoto (efêmero). Local, o dev cuida do próprio setup.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Idempotente: instala só se ainda não estiver disponível.
if ! python3 -c "import weasyprint" 2>/dev/null; then
  pip install --quiet weasyprint >/dev/null 2>&1 || pip install --quiet --break-system-packages weasyprint >/dev/null 2>&1
fi
