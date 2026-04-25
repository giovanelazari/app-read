# Kindle Highlights PWA

Sistema pessoal para capturar, revisar e relembrar grifos do Kindle (dispositivo + app).

---

## 1. Visão geral

Quatro modos simultâneos:

1. **Diário passivo** — 1 grifo aleatório enviado via push toda manhã (08:00).
2. **Repetição espaçada (SRS)** — revisão 3x/semana (seg/qua/sex 19:00) com algoritmo SM-2. O usuário avalia cada grifo de 0 a 5 e o sistema reagenda.
3. **Feed por tag** — grifos podem ser taggeados (`delegação`, `vendas`, …) e consultados como matéria-prima.
4. **Modo foco** — um livro vira a fonte principal dos próximos N dias (modos `replace` / `augment`, ordem `sequential` / `random`).

Arquitetura:

```
iPhone (Safari/PWA) ──HTTPS──► Traefik (existente) ──► web (nginx SPA)
                                                  └──► api (FastAPI)
                                                             ├─ Postgres (volume)
                                                             ├─ APScheduler (cron in-process)
                                                             ├─ Playwright (volume: sessão Amazon)
                                                             └─ pywebpush (VAPID → iOS/Chrome)
```

Stack: Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, APScheduler, Playwright, PostgreSQL 16, React 18 + Vite + Tailwind + vite-plugin-pwa, Docker Swarm.

---

## 2. Pré-requisitos

**No VPS:**
- Docker Engine com Swarm inicializado (`docker swarm init` ou já membro de um swarm)
- Traefik v2 já rodando como serviço swarm, watching uma network externa, com um certresolver Let's Encrypt configurado
- Dois subdomínios (web + api) com A records apontando pro IP público do VPS

**Localmente (na sua máquina):**
- Python 3.11 com venv (pra fazer o primeiro login na Amazon)
- `rsync` ou `scp` (pra subir a sessão Playwright pro VPS)

---

## 3. DNS

Crie 2 A records no painel da sua hospedagem (Hostinger, Cloudflare, etc.):

| Tipo | Nome         | Valor (IP do VPS) | TTL    |
|------|--------------|-------------------|--------|
| A    | `kindle`     | `<IP do VPS>`     | 300    |
| A    | `kindle-api` | `<IP do VPS>`     | 300    |

Depois, do seu laptop, espere a propagação:

```bash
dig +short kindle.seudominio.com
dig +short kindle-api.seudominio.com
# ambos devem retornar o IP do VPS
```

---

## 4. Primeira execução — login Amazon (CRÍTICO)

A sessão do Amazon precisa ser iniciada localmente (modo headed, com 2FA) antes de subir o container headless no VPS.

### 4.1 Setup Python local

```bash
git clone https://github.com/giovanelazari/app-read.git kindle-app
cd kindle-app

cd api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cd ..
```

### 4.2 Subir só o Postgres local pra registrar o sync

```bash
cp .env.example .env
# edite .env: troque POSTGRES_PASSWORD pra algo forte; deixe os hosts/email como estão
docker compose up -d db
```

### 4.3 Aplicar migrations e rodar o scraper headed

```bash
cd api
source .venv/bin/activate
DATABASE_URL=postgresql+psycopg://kindle:SUASENHA@localhost:5432/kindle_highlights \
  alembic upgrade head

DATABASE_URL=postgresql+psycopg://kindle:SUASENHA@localhost:5432/kindle_highlights \
  HEADED=1 \
  PLAYWRIGHT_PROFILE_DIR=$PWD/../data/playwright/profile \
  python -m app.scraper.run --headed
```

O Chromium abre. Faça login + 2FA. Quando a página `kp/notebook` aparecer, o scraper extrai tudo. A pasta `data/playwright/profile/` (na raiz do repo) fica com os cookies.

### 4.4 Subir a sessão pro VPS

```bash
cd ..  # de volta pra raiz do repo
rsync -av data/playwright/ root@31.97.130.40:/opt/kindle-app/data/playwright/
```

---

## 5. Deploy no VPS (Docker Swarm)

```bash
ssh root@31.97.130.40
mkdir -p /opt/kindle-app
cd /opt/kindle-app
git clone https://github.com/giovanelazari/app-read.git .
cp .env.example .env

# Edite .env com a MESMA senha de POSTGRES_PASSWORD usada localmente,
# e confirme que TRAEFIK_NETWORK + TRAEFIK_CERTRESOLVER batem com seu Traefik.
nano .env

./deploy.sh
```

O `deploy.sh` cuida de:
1. Validar que a network do Traefik existe
2. Buildar `kindle-api:latest` e `kindle-web:latest` localmente
3. `docker stack deploy -c docker-compose.stack.yml kindle`
4. Migrations rodam automaticamente quando o container `api` sobe (entrypoint chama `alembic upgrade head`)

Verifique:

```bash
docker service ls | grep kindle
# kindle_db    replicated   1/1   postgres:16-alpine
# kindle_api   replicated   1/1   kindle-api:latest
# kindle_web   replicated   1/1   kindle-web:latest

docker service logs -f kindle_api
# espera ver: "Uvicorn running on http://0.0.0.0:8000"

curl -I https://kindle-api.seudominio.com/healthz
# HTTP/2 200
```

Se o cert TLS demorar > 2 min, veja os logs do Traefik:

```bash
docker service logs traefik_traefik 2>&1 | tail -50
```

---

## 6. Instalar no iPhone

1. Abra `https://kindle.seudominio.com` no **Safari** (push no iOS exige Safari).
2. Toque em **Compartilhar → Adicionar à Tela Inicial**.
3. Abra pelo ícone na home (modo standalone).
4. Vá em **Configurações → Ativar notificações** e aceite o prompt.
5. Pronto. Push diário 08:00 e lembrete de revisão seg/qua/sex 19:00.

> ⚠️ No iOS, `Notification.requestPermission()` só funciona depois do app estar na tela inicial.

---

## 7. Operação

### Atualizar código (deploy de uma nova versão)

```bash
ssh root@31.97.130.40
cd /opt/kindle-app
git pull
./deploy.sh
```

O Swarm faz rolling update — a app fica disponível durante o deploy.

### Renovar sessão Amazon

Quando você receber o push **"Sessão Amazon expirou"** (ou `status: auth_required` em Configurações):

```bash
# Localmente:
cd kindle-app/api
source .venv/bin/activate
HEADED=1 python -m app.scraper.run --headed

# Suba a sessão renovada:
cd ..
rsync -av data/playwright/ root@31.97.130.40:/opt/kindle-app/data/playwright/

# No VPS:
ssh root@31.97.130.40
docker service update --force kindle_api
```

### Logs

```bash
docker service logs -f kindle_api
docker service logs -f kindle_web
docker service logs -f kindle_db
```

### Sincronização

- Automática: todo dia às 06:00 (America/Sao_Paulo).
- Manual: botão **Sincronizar agora** em Configurações, ou `POST /sync`.

### Backup

Faça snapshot de:

- Volume `kindle_kindle_postgres` — todo o banco
- `/opt/kindle-app/data/playwright/` — sessão Amazon
- Volume `kindle_kindle_vapid` — chaves VAPID (se perder, todos dispositivos precisam re-inscrever)

Para backup do banco:

```bash
docker exec -it $(docker ps -q -f name=kindle_db) \
  pg_dump -U kindle kindle_highlights > backup_$(date +%F).sql
```

---

## 8. Decisões tomadas

- **Docker Swarm em vez de Compose puro** porque o Traefik existente do VPS roda em modo swarm provider — só descobre serviços swarm. Stack file separado (`docker-compose.stack.yml`) pra produção; `docker-compose.yml` simples pra dev local.
- **Postgres próprio em vez de reusar o pgvector existente** — isolamento. ~100MB de RAM extra por consciência tranquila.
- **Migrations no entrypoint** (`api/docker-entrypoint.sh`) em vez de job separado. Idempotente, simplifica o swarm.
- **Build local de imagens, sem registry**. Pra um swarm de 1 nó, é o caminho mais simples. Se você expandir pra múltiplos nodes, daí faz sentido registrar no GHCR.
- **Idempotência via `ON CONFLICT DO NOTHING`** com unique em `(book_id, location, text)`. Rodar sync 5x não duplica.
- **SM-2 com EF preservado em falha** — variante padrão Anki, evita punir itens novos duas vezes.
- **Timezone `America/Sao_Paulo`** fixado em Postgres, APScheduler e formatação do frontend.
- **Service Worker via `injectManifest`** — controle total do `push` / `notificationclick`.
- **Sem autenticação no MVP** — atrás de Traefik, uso pessoal. Pra expor publicamente, adicione middleware Basic Auth no Traefik.

---

## 9. Endpoints REST

```
GET    /highlights/today                  1 grifo (respeita foco ativo)
GET    /highlights/random                 1 aleatório global
GET    /highlights/review-queue?limit=10  grifos vencidos no SRS
POST   /highlights/{id}/review            body {ease: 0-5}
GET    /highlights/by-tag/{tag}
POST   /highlights/{id}/tags              body {tags: [...]}
DELETE /highlights/{id}/tags/{tag}

GET    /books                             lista + count + last_synced
GET    /books/{id}
GET    /books/{id}/highlights

GET    /focus
POST   /focus
DELETE /focus

GET    /tags
POST   /tags

POST   /push/subscribe
DELETE /push/subscribe
GET    /push/vapid-public-key

POST   /sync
GET    /sync/status

GET    /healthz
```

Swagger UI em `https://kindle-api.seudominio.com/docs`.

---

## 10. Troubleshooting

**Push não chega no iPhone:**
1. Confirme que o app foi aberto pelo ícone da home (sem URL no topo).
2. iOS 16.4+ é necessário pra Web Push.
3. Confirme HTTPS válido. Service Workers não rodam em HTTP nem com cert self-signed.
4. `docker service logs kindle_api | grep push`. Se subscribers foram registrados, o problema é entrega ou VAPID.

**Cert Let's Encrypt não emite:**
- Confirme que o A record propagou (`dig +short kindle.seudominio.com`).
- Veja `docker service logs traefik_traefik` — Let's Encrypt loga rate limit, DNS errors, etc.
- Você tem 5 emissões/semana por domínio. Em testes, use o staging server.

**Scraper trava em "auth_required":**
- Rode local com `HEADED=1`, faça 2FA, `rsync` da pasta de sessão, `docker service update --force kindle_api`.

**Stack não sobe / "no such network network_swarm_public":**
- Confirme que o Traefik está rodando: `docker service ls | grep traefik`.
- Confirme o nome da network: `docker network ls | grep swarm_public`.
- Se for outro nome, ajuste `TRAEFIK_NETWORK` no `.env`.

**Web carrega mas chamadas API falham com CORS:**
- O `WEB_URL` no `.env` precisa ser EXATAMENTE o origin do frontend (com `https://`, sem barra final). O CORS no FastAPI lê esse valor.
