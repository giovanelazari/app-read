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
iPhone (Safari/PWA) ──HTTPS──► Traefik ──► web (nginx SPA)
                                      └──► api (FastAPI)
                                                 ├─ Postgres (volume)
                                                 ├─ APScheduler (cron in-process)
                                                 ├─ Playwright (volume: sessão Amazon)
                                                 └─ pywebpush (VAPID → iOS/Chrome)
```

Stack: Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, APScheduler, Playwright, PostgreSQL 16, React 18 + Vite + Tailwind + vite-plugin-pwa, Docker Compose.

---

## 2. Pré-requisitos no VPS

- Docker + Docker Compose plugin
- Traefik rodando com resolver Let's Encrypt (ajustar `TRAEFIK_CERTRESOLVER` e `TRAEFIK_NETWORK` no `.env` conforme sua convenção)
- Dois subdomínios apontando para o IP do VPS (ex.: `kindle.seudominio.com` e `kindle-api.seudominio.com`), ambos com A records

> Sem auth no MVP — uso pessoal. Se for expor para público, adicione Basic Auth no Traefik:
> ```
> labels:
>   - "traefik.http.routers.kindle-api.middlewares=kindle-auth"
>   - "traefik.http.middlewares.kindle-auth.basicauth.users=usuario:$$apr1$$..."
> ```

---

## 3. Setup local

```bash
git clone <repo>
cd kindle-app
cp .env.example .env
# edite .env: defina POSTGRES_PASSWORD forte, hosts, e-mail VAPID
```

---

## 4. Primeira execução — login Amazon (passo CRÍTICO)

A sessão do Amazon precisa ser iniciada localmente (headed) antes de subir o container headless.

### 4.1 Setup Python local

```bash
cd api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 4.2 Rode o scraper em modo visível

Aponte o `DATABASE_URL` para um Postgres local ou, mais simples, suba apenas o `db` do Compose primeiro e conecte no localhost:

```bash
cd ..
docker compose up -d db
# do host, o Postgres fica em localhost:5432 (adicione "ports: [5432:5432]" no db se necessário,
# ou rode o scraper dentro do container via docker compose run, veja abaixo).
```

Ou, sem expor o Postgres, rode o scraper dentro do container — mas montando X11:
no macOS/Windows é mais prático rodar localmente com um Postgres local ou pular o DB desse run (o scraper grava em log mas pode rodar sem DB se você adaptar). O fluxo recomendado: usar um DB local rápido só para o primeiro run.

Uma vez configurado:

```bash
cd api
HEADED=1 python -m app.scraper.run
```

O Chromium abre. Faça login, complete 2FA. O scraper extrai tudo e a pasta `data/playwright/profile` fica com os cookies.

### 4.3 Suba a sessão para o VPS

```bash
# da raiz do repo, na sua máquina:
rsync -av data/playwright/ usuario@vps:~/kindle-app/data/playwright/
```

---

## 5. Subir a stack no VPS

```bash
ssh usuario@vps
cd ~/kindle-app
cp .env.example .env   # edite igual ao local
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose up -d api web
```

Verifique:

```bash
curl https://kindle-api.seudominio.com/healthz   # {"ok": true}
```

---

## 6. Instalar no iPhone

1. Abra `https://kindle.seudominio.com` no **Safari** (não Chrome — push no iOS requer Safari).
2. Toque em **Compartilhar → Adicionar à Tela Inicial**.
3. Abra o app pelo ícone da home (modo standalone).
4. Vá em **Configurações → Ativar notificações** e aceite o prompt.
5. Pronto. Um push chega 08:00 (grifo do dia) e seg/qua/sex 19:00 (lembrete de revisão).

> ⚠️ No iOS, `Notification.requestPermission()` só funciona depois do app estar na tela inicial. O app detecta e avisa.

---

## 7. Operação

### Renovar sessão Amazon

Quando você receber o push **"Sessão Amazon expirou"** (ou ver `status: auth_required` em Configurações):

```bash
cd api
HEADED=1 python -m app.scraper.run
rsync -av data/playwright/ usuario@vps:~/kindle-app/data/playwright/
docker compose restart api
```

### Logs

```bash
docker compose logs -f api
docker compose logs -f web
```

### Sincronização

- Automática: todo dia às 06:00 (America/Sao_Paulo).
- Manual: botão **Sincronizar agora** em Configurações, ou `POST /sync`.

### Backup

Só faça backup de:

- `data/postgres/` — todo o banco
- `data/playwright/` — sessão Amazon
- `data/vapid/` — chaves VAPID (se perder, os dispositivos precisarão se re-inscrever)

---

## 8. Decisões tomadas

- **Scraper como módulo do API**, não container separado. Simplifica o setup (1 imagem Docker com Playwright), as migrations, e o acesso ao DB via `SessionLocal`.
- **Idempotência via `ON CONFLICT DO NOTHING`** com unique em `(book_id, location, text)`. Rodar 5x em sequência não duplica.
- **SM-2 com EF preservado em falha** — evita punir itens novos duas vezes. Variante padrão na maioria das implementações modernas de Anki.
- **Timezone `America/Sao_Paulo`** fixado no Postgres, no APScheduler e no frontend (via `toLocaleString`).
- **Service Worker via `injectManifest`** — damos control total do `push` / `notificationclick` sem depender das estratégias genéricas de Workbox.
- **Ícones PNG mono-color como placeholder**. Substitua `web/public/icon-*.png` por arte real antes de lançar.
- **Sem autenticação no MVP** — uso pessoal atrás de Traefik. README aponta como adicionar Basic Auth.

---

## 9. Endpoints REST

```
GET    /highlights/today                  1 grifo (respeita foco ativo)
GET    /highlights/random                 1 aleatório global
GET    /highlights/review-queue?limit=10  grifos vencidos no SRS
POST   /highlights/{id}/review            body {ease: 0-5}
GET    /highlights/by-tag/{tag}           paginado
POST   /highlights/{id}/tags              body {tags: [...]}
DELETE /highlights/{id}/tags/{tag}

GET    /books                             lista + count + last_synced
GET    /books/{id}
GET    /books/{id}/highlights             paginado

GET    /focus                             sessão ativa ou null
POST   /focus                             {book_id, days, intensity, mode, order_mode}
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
1. Confirme que o app foi aberto pelo ícone da home (barra de status deve ser escura, sem URL).
2. iOS 16.4+ (necessário para Web Push).
3. Confirme HTTPS com cert válido. Service Workers não rodam em HTTP nem com cert self-signed.
4. Veja `docker compose logs api | grep push` — se subscriber foi registrado, o problema é na entrega (Apple) ou no VAPID.

**Scraper trava em "Not logged in":**
- Rode local com `HEADED=1`, complete 2FA, depois `rsync` da pasta `data/playwright/`.

**Duplicação de grifos:**
- Não deveria ocorrer por causa do unique constraint. Se ocorrer, verifique se o texto mudou (Amazon às vezes renormaliza espaços).
