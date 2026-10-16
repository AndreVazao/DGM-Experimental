# Pacote Windows DGM-MAT — back-office e dashboard

Este pacote é produzido manualmente pelo workflow **Windows Back-office and Dashboard Build**. O workflow não corre automaticamente em cada push ou PR.

## Conteúdo

- engine/DGM-MAT-BackOffice.exe e dependências PyInstaller: back-office em modo headless.
- dashboard/index.html, app.js, styles.css: frontend PC, sem npm nem serviços pagos.
- Install-DGM-MAT.ps1: instalador explícito para todos os utilizadores deste Windows.
- BUILD.txt: commit e execução de origem do pacote.

## Instalação

1. Extrai o ZIP para uma pasta local.
2. Clica com o botão direito em Install-DGM-MAT.ps1 e escolhe **Executar com PowerShell**. O instalador pede UAC para instalar em Program Files e criar atalhos comuns.
3. Depois da instalação, termina e volta a iniciar sessão ou reinicia o PC.
4. O back-office arranca oculto quando qualquer utilizador inicia sessão. O launcher consulta primeiro http://127.0.0.1:8181/health para evitar iniciar outra cópia se a API já responder.
5. O dashboard **não** abre sozinho. Clica em **DGM-MAT Dashboard** no Ambiente de Trabalho Público; abre http://127.0.0.1:8181/app/.

O instalador define a variável de máquina DGM_MOBILE_UI_PATH para a pasta local do dashboard porque o backend atual usa esse nome legado para localizar a interface PC.

## Limites e validação

- O workflow testa os módulos focados do executor/auditoria/segurança e os contratos Node do dashboard antes de empacotar.
- O build é onedir, não um executável autónomo: mantém DLLs e dependências ao lado do EXE.
- O pacote não instala Ollama, Claude Code, Git, credenciais ou browsers, não eleva o back-office e não executa comandos arbitrários.
- O arranque comum acontece no início de sessão de qualquer utilizador, não antes do ecrã de login do Windows.
- O endpoint de saúde, a autenticação, o carregamento do frontend e o comportamento em Windows têm de ser verificados no PC alvo. A criação do artefacto, por si só, não prova que a aplicação está operacional.
- Os dados de utilizador não são apagados pelo instalador. Se existir uma instalação anterior, os ficheiros do motor são copiados para backups/pre-update-<data> antes de serem substituídos.
