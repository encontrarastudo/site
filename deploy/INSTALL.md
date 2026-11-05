# Painel admin — Encontrarás Tudo (instalação na VPS)

Serve em https://admin.encontrarastudo.com.br. Edita orações/novenas e publica o
site estático (regenera /var/www/encontrarastudo). Caddy e Listmonk não são tocados.

## 1. DNS (Registro.br)
Adicione um registro A:  admin  →  165.232.86.154

## 2. Subir os arquivos (do seu PC)
    scp encontrarastudo-admin.tar.gz root@165.232.86.154:/root/

## 3. No droplet — instalar
    mkdir -p /opt/encontrarastudo-admin
    tar -xzf /root/encontrarastudo-admin.tar.gz -C /tmp
    cp -r /tmp/admin-pkg/* /opt/encontrarastudo-admin/
    cd /opt/encontrarastudo-admin
    apt-get update && apt-get install -y python3-venv
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt

## 4. Configurar senha
    cp deploy/admin.env.example admin.env
    nano admin.env        # defina ADMIN_PASSWORD e ADMIN_SECRET
    chmod 600 admin.env

## 5. Serviço (systemd)
    cp deploy/encontrarastudo-admin.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable --now encontrarastudo-admin
    systemctl status encontrarastudo-admin --no-pager | head -5

## 6. Caddy (subdomínio com HTTPS automático)
    cat deploy/Caddyfile.admin >> /etc/caddy/Caddyfile
    caddy validate --config /etc/caddy/Caddyfile
    systemctl reload caddy

## 7. Usar
Abra https://admin.encontrarastudo.com.br, faça login, edite e clique em "Publicar site".

## Observações
- A partir daqui, a FONTE do conteúdo é /opt/encontrarastudo-admin/data/*.json.
- Fazer backup: basta copiar a pasta /opt/encontrarastudo-admin (dados + imagens).
- Para trocar a senha: edite admin.env e rode `systemctl restart encontrarastudo-admin`.
