# site — encontrarastudo.com.br

Fonte do site, publicada automaticamente. NÃO editar à mão em produção.
O conteúdo é gerado pelo pipeline (Claude) e aprovado pelo Gustavo.

- `build_pages.py` / `build_oracoes.py` — geradores do site estático
- `data/*.json` — conteúdo (oracoes, novenas, artigos, produtos, materiais, config)
- `assets/` — estilos, imagens, materiais (PDFs)
- `deploy.sh` — rodado por cron no servidor: `git pull` + rebuild quando há commit novo
