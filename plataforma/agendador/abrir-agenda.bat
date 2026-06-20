@echo off
REM Dispara o AVISO: abre a Agenda do painel e mostra um popup.
REM Na Agenda, a tarefa vencida (ex: proximo lote da campanha) aparece com
REM o botao Confirmar. Voce clica e o lote sai pronto. Nada envia sozinho.
start "" "http://127.0.0.1:5000/agenda"
msg "%USERNAME%" /TIME:900 "MazyOS: hora de checar a Agenda. Confirme o proximo lote da campanha no painel."
