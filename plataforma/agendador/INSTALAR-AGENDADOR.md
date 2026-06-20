# Agendador do SO — o despertador da Agenda

O painel mostra o aviso e o botão Confirmar, mas só com ele aberto. Este
agendador é o **despertador**: de hora em hora (em horário comercial) ele
abre a Agenda do painel e dá um popup, pra você só clicar **Confirmar** e o
lote da campanha sair pronto. Nada é enviado sozinho.

## Como funciona o fluxo completo
1. Uma vez: no painel, em **⏰ Agenda**, clique **"Agendar campanha"** (cria a
   tarefa recorrente "próximo lote", de hora em hora).
2. O agendador do Windows abre a Agenda a cada hora (9h–18h, dias úteis).
3. A tarefa aparece em **🔔 Vencidas** → você clica **Confirmar** → saem 4
   mensagens prontas e elas são marcadas no funil.
4. Você manda as 4 espaçadas. Quando os celulares acabarem, a campanha encerra.

---

## Windows (Agendador de Tarefas) — copie e cole no Prompt de Comando

> Antes: troque `C:\Users\Mario\MazyOS` pelo caminho real do projeto na sua
> máquina (onde está a pasta `plataforma`).

**1) Manter o painel rodando (inicia no logon):**
```bat
schtasks /Create /TN "MazyOS Painel" /SC ONLOGON ^
  /TR "\"C:\Users\Mario\MazyOS\plataforma\agendador\iniciar-painel.bat\""
```

**2) Despertador da Agenda — de hora em hora, 9h às 18h, segunda a sexta:**
```bat
schtasks /Create /TN "MazyOS Agenda" /SC WEEKLY /D MON,TUE,WED,THU,FRI ^
  /ST 09:00 /RI 60 /DU 09:00 /K ^
  /TR "\"C:\Users\Mario\MazyOS\plataforma\agendador\abrir-agenda.bat\""
```
- `/RI 60` repete a cada 60 min · `/DU 09:00` por 9 horas (até as 18h) · `/K`
  encerra no fim da janela.

**Versão simples (se a de cima reclamar):** toda hora, o dia todo:
```bat
schtasks /Create /TN "MazyOS Agenda" /SC HOURLY /ST 09:00 ^
  /TR "\"C:\Users\Mario\MazyOS\plataforma\agendador\abrir-agenda.bat\""
```

**Testar agora (sem esperar a hora):**
```bat
schtasks /Run /TN "MazyOS Agenda"
```

**Remover depois:**
```bat
schtasks /Delete /TN "MazyOS Agenda" /F
schtasks /Delete /TN "MazyOS Painel" /F
```

---

## Linux / macOS (cron) — alternativa

`crontab -e` e adicione (de hora em hora, 9h–18h, seg–sex):
```cron
# Linux
0 9-18 * * 1-5  xdg-open http://127.0.0.1:5000/agenda
# macOS
0 9-18 * * 1-5  open http://127.0.0.1:5000/agenda
```
Pra manter o painel rodando, inicie `python plataforma/app.py` no login
(Aplicativos de inicialização) ou rode num terminal aberto.

---

## Observações
- O despertador **só abre a Agenda**; quem dispara a ação é você, no Confirmar.
  É de propósito: cold outreach precisa de revisão humana (LGPD/ToS + anti-ban).
- Se preferir não depender do SO, dá pra usar um **trigger agendado no Claude
  Code na web** apontando pro mesmo comando (`/campanha`). Ver a skill
  `/campanha`, seção "Modo rotina".
- O cadência de 1 lote/hora respeita a regra anti-ban (~4 mensagens por hora).
